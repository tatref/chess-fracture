#![feature(plugin)]
#![plugin(rocket_codegen)]
#![feature(custom_derive)] 
#![allow(dead_code)]
#![allow(unused_imports)]

extern crate rocket;
extern crate rocket_contrib;
#[macro_use] extern crate serde_derive;
extern crate url;
extern crate regex;
extern crate reqwest;
#[cfg(test)] #[macro_use] extern crate lazy_static;
#[macro_use] extern crate crossbeam_channel;


use crossbeam_channel as channel;


mod test;



mod fracture_chess {
    //use rocket::Request;
    //use rocket::http::Cookies;
    use regex::Regex;
    use reqwest;
    use rocket::http::RawStr;
    use rocket::request::Form;
    use rocket::request::FormItems;
    use rocket::request::FromForm;
    use rocket::response::Redirect;
    use rocket;
    use rocket_contrib::Template;
    use url::Url;

    const BLEND_FILES_URL_PREFIX: &str = "/blend";
    const BLEND_FILES_SAVE_PATH: &str = "/blend";
    const PGN_SAVE_PATH: &str = "/pgn";
    
    #[get("/webapp")]
    fn index() -> Template {
        use std::collections::HashMap;
        let mut context = HashMap::new();
        context.insert(0, 0);

        Template::render("index", &context)
    }

    #[derive(Clone, Debug, Hash)]
    enum Site {
        Lichess,
    }

    impl<'a> rocket::request::FromParam<'a> for Site {
        type Error = ();

        fn from_param(param: &'a RawStr) -> Result<Self, Self::Error> {
            match param.as_str() {
                "Lichess" => Ok(Site::Lichess),
                _ => Err(()),
            }
        }
    }
    
    /// check the provided URL and fix it to a correctl PGN URL
    fn get_pgn_download_url(url: &Url) -> Result<PgnUrl, ()> {
        match url.domain() {
            Some("lichess.org") => {
                // Game URL: https://lichess.org/xxxxx/white#2
                // PGN URL:  https://lichess.org/game/export/xxxx.pgn
                let re = Regex::new(r"^https://lichess.org/(?P<gameid>[[:alnum:]]+)(/(white|black)(#\d+)?)?$")
                    .unwrap();
                let game_id = re.captures(url.as_str())
                    .ok_or(())?
                    .name("gameid")
                    .unwrap()  // always succeeds
                    .as_str();

                return Ok( PgnUrl { site: Site::Lichess, game_id: game_id.into() });
            },
            Some(_) => Err(()),
            _ => Err(()),
        }
    }

    #[derive(Clone, Debug)]
    struct PgnUrl {
        site: Site,
        game_id: String,
    }
    
    impl<'f> FromForm<'f> for PgnUrl {
        type Error = ();
    
        fn from_form(items: &mut FormItems<'f>, strict: bool) -> Result<PgnUrl, ()> {
            for (key, value) in items {
                match key.as_str() {
                    "url" => {
                        let url = value.url_decode()
                            .map_err(|_| ())?
                            .parse::<Url>()
                            .map_err(|_| ())?;
    
                        return get_pgn_download_url(&url);
                    },
                    _ if strict => return Err(()),
                    _ => { /* allow extra value when not strict */ }
                }
            }
    
            return Err(())
        }
    }

    #[derive(Copy, Clone, Debug, Hash)]
    enum BlenderResult {
        Success,
        Failure,
    }

    use crossbeam_channel::{Sender, Receiver};
    fn run_blender(state: &State<RwLock<WebappState>>, site: &Site, game_id: &str, pgn_path: &str) {
        use std::env::var;
        let username = var("USER").unwrap();

        let chess_fracture_out_blend = format!("{}/{:?}_{}.blend", BLEND_FILES_SAVE_PATH, &site, &game_id);
        use std::fs;
        if let Err(_) = fs::metadata(&chess_fracture_out_blend) {  // prevent resubmiting
            use std::process::Command;
            use std::process::Stdio;

            // CHESS_FRACTURE_OUT_BLEND=out.blend DISPLAY=:1 CHESS_FRACTURE_PGN_PATH=game.pgn CHESS_FRACTURE_TEST= blender chess_fracture_template.blend -noaudio --addons object_fracture_cell --python chess_fracture.py 
            let cmd = Command::new(&format!("/home/{}/blender-2.79b-linux-glibc219-x86_64/blender", username))
                .stdout(Stdio::inherit())
                .stderr(Stdio::inherit())
                .arg(&format!("/home/{}/chess-fracture/blender/chess_fracture_template.blend", username))
                .arg("-noaudio")
                .arg("--addons")
                .arg("object_fracture_cell")
                .arg("--python")
                .arg(&format!("/home/{}/chess-fracture/blender/chess_fracture.py", username))
                .env("CHESS_FRACTURE_OUT_BLEND", &chess_fracture_out_blend)
                .env("DISPLAY", ":1")
                .env("CHESS_FRACTURE_PGN_PATH", &pgn_path)
                .env("CHESS_FRACTURE_TEST", "")
                .spawn()
                .expect("call to blender failed");

            cmd.wait_with_output().expect("fooo");
            //if cmd.status.success() {
            //    println!("exec blender ok");
            //}
            //else {
            //    println!("failed");
            //    println!("stdout: {:?}", &cmd.stdout);
            //    println!("stderr: {:?}", &cmd.stderr);
            //}
        }
        //outcome.send(BlenderResult::Success)
    }
    
    /// this is the input
    #[post("/webapp/post", format = "application/x-www-form-urlencoded", data = "<pgnurl>")]
    fn post(pgnurl: Form<PgnUrl>, state: State<RwLock<WebappState>>) -> Result<Redirect, String> {
        let PgnUrl { site, game_id } = pgnurl.into_inner();

        let mut pgn_name = String::from(game_id.clone());
        pgn_name.push_str(".pgn");
        
        let base_url = Url::parse("https://lichess.org/game/export/")
            .unwrap();  // always succeeds
        let pgn_url = base_url.join(&pgn_name).unwrap();
        let mut response = reqwest::get(pgn_url.clone())
            .unwrap();
        let pgn = match response.status().is_success() {
            true => {
                response
                    .text()
                    .unwrap()
            },
            false => {
                return Err(format!("wget '{}' failed", &pgn_url));
            },
        };

        if pgn == "Can't export PGN of game in progress" {
            return Err("Can't export PGN of game in progress".into())
        }

        use std::fs::File;
        use std::io::prelude::*;
        let pgn_path = format!("{}/{:?}_{}", PGN_SAVE_PATH, &site, &game_id);
        let mut f = File::create(&pgn_path).expect(&format!("Can't create file {}", &pgn_path));
        f.write_all(pgn.as_bytes()).expect("Can't write to file");
        f.flush().expect("Can't write to file");
        println!("PGN dumped to {:?}", f);

        run_blender(&state, &site, &game_id, &pgn_path);

        let redirect_url = format!("/webapp/get/{:?}/{}", &site, game_id);
        Ok(Redirect::to(&redirect_url))
    }

    /// check if the blender process exited and successfully generated the blend file
    fn simulation_finished(_site: &Site, _game_id: &str) -> bool {
        // TODO
        true
    }

    use std::collections::HashMap;
    use std::thread::JoinHandle;
    struct WebappState {
        inner: HashMap<usize, usize>,
        threads: HashMap<String, Receiver<BlenderResult>>,
    }

    use rocket::request::State;
    use std::sync::RwLock;
    /// Retrieve a blend file or wait if not computed yet
    #[get("/webapp/get/<site>/<game_id>")]
    fn get(site: Site, game_id: String, state: State<RwLock<WebappState>>) -> Result<Template, String> {
        if simulation_finished(&site, &game_id) {
            use std::collections::HashMap;

            let blend_link = format!("{}/{:?}_{}.blend", BLEND_FILES_URL_PREFIX, &site, &game_id);
            //let mut rw_state = state.write().unwrap();
            //use std::thread;
            //let thread_handle = thread::spawn(|| { println!("hello from thread"); });
            //rw_state.threads.insert("coucou".into(), thread_handle);

            //*rw_state.inner.get_mut(&0).unwrap() += 1;

            let mut context = HashMap::new();
            context.insert("blend_link", blend_link);
            //context.insert("value", format!("{:?}", rw_state.inner.get(&0).unwrap()));

            Ok(Template::render("get", &context))
        }
        else {
            // TODO: wait + autorefresh
            Err("Not finished...".to_string())
        }
    }

    pub fn rocket_chess() -> rocket::Rocket {
        use rocket::config::{Config, Environment};
        
        let config = Config::build(Environment::Staging)
            .address("127.0.0.1")
            .port(8000)
            .finalize()
            .unwrap();

        use std::collections::HashMap;
        let mut webapp_state = WebappState { inner: HashMap::new(), threads: HashMap::new()};
        webapp_state.inner.insert(0, 0);
        
        rocket::custom(config, true)
            .mount("/", routes![index, get, post])
            .attach(Template::fairing())
            .manage(RwLock::new(webapp_state))
    }

    pub fn run() {
        rocket_chess()
            .launch();
    }
}

fn main() {
    fracture_chess::run();
}


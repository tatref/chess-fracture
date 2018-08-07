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
    
    #[get("/")]
    fn index() -> Template {
        use std::collections::HashMap;
        let mut context = HashMap::new();
        context.insert(0, 0);

        Template::render("index", &context)
    }

    #[derive(Clone, Copy, Debug, Hash, Eq, PartialEq)]
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
        AlreadySimulated,
    }

    use crossbeam_channel::{Sender, Receiver};
    fn run_blender(s: Sender<BlenderResult>, site: &Site, game_id: String, pgn_path: &str) {
        use std::env::var;
        let username = var("USER").unwrap();

        let chess_fracture_out_blend = format!("{}/{:?}_{}.blend", BLEND_FILES_SAVE_PATH, &site, &game_id);

        //{
        //    let mut_state = &mut state.write().expect("Unable to open state");
        //    mut_state.stats.current_running += 1;
        //}

        use std::fs;
        if fs::metadata(&chess_fracture_out_blend).is_ok() {
            //let mut_state = &mut state.write().expect("Unable to open state");
            //mut_state.stats.current_running -= 1;
            //let outcome = &mut_state.threads[&(*site, game_id.into())].0;
            //outcome.send(BlenderResult::AlreadySimulated);
            s.send(BlenderResult::AlreadySimulated);
            return;
        }

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
            //.env("CHESS_FRACTURE_TEST", "")
            //.env("CHESS_FRACTURE_FRAMES_PER_MOVE", "20")
            //.env("CHESS_FRACTURE_FRAGMENTS", "10")
            .spawn()
            .expect("call to blender failed");

        cmd.wait_with_output().expect("fooo");

        //let mut_state = &mut state.write().expect("Unable to open state");
        //mut_state.stats.current_running -= 1;
        //mut_state.stats.total_runs += 1;
        //let outcome = &mut_state.threads[&(*site, game_id.into())].0;
        //outcome.send(BlenderResult::Success);
        s.send(BlenderResult::Success);
        drop(s);
    }
    
    /// this is the input
    #[post("/post", format = "application/x-www-form-urlencoded", data = "<pgnurl>")]
    fn post(pgnurl: Form<PgnUrl>, state: State<RwLock<WebappState>>) -> Result<Redirect, String> {
        let PgnUrl { site, game_id } = pgnurl.into_inner();

        let redirect_url = format!("/webapp/get/{:?}/{}", &site, game_id);
        if state.read().expect("Unable to read state").threads.contains_key(&(site, game_id.clone())) {
            // prevent resubmits
            return Ok(Redirect::to(&redirect_url));
        }

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

        use crossbeam_channel as channel;
        let (s, r) = channel::bounded(1);
        &state.write().expect("Unable to write state").threads.insert((site, game_id.clone()), (s.clone(), r));

        use std::thread;
        let xx = game_id.clone();
        thread::spawn( move || {
            run_blender(s, &site, xx, &pgn_path);
        });

        Ok(Redirect::to(&redirect_url))
    }

    #[derive(Debug, Copy, Clone)]
    enum SimulationStatus {
        Running,
        Finished,
        NotRunning,
        Failed,
    }

    /// check if the blender process exited and successfully generated the blend file
    fn simulation_status(site: &Site, game_id: String, state: State<RwLock<WebappState>>) -> SimulationStatus {
        // 1) check file /blend/...
        use std::fs;
        let chess_fracture_out_blend = format!("{}/{:?}_{}.blend", BLEND_FILES_SAVE_PATH, &site, &game_id);
        if fs::metadata(&chess_fracture_out_blend).is_ok() {
            return SimulationStatus::Finished;
        }

        // 2) try_recv
        let read_state = state.read().expect("Unable to read state");
        let entry = read_state.threads.get(&(*site, game_id.clone()));
        match entry {
            Some(x) => {
                match x.1.try_recv() {
                    Some(xx) => {
                        match xx {
                            BlenderResult::Success => SimulationStatus::Finished,
                            BlenderResult::Failure => SimulationStatus::Failed,
                            BlenderResult::AlreadySimulated => SimulationStatus::Finished,
                        }
                    },
                    None => SimulationStatus::Running,  // TODO: if the channel is closed??
                }
            },
            None => SimulationStatus::NotRunning,
        }
    }

    #[derive(Debug)]
    struct WebappStats {
        total_runs: u32,
        current_running: u32,
    }
    #[get("/stats")]
    fn stats(state: State<RwLock<WebappState>>) -> String {
        format!("{:?}", state.read().expect("Unable to read state").stats)
    }

    use std::collections::HashMap;
    use std::thread::JoinHandle;
    struct WebappState {
        stats: WebappStats,
        threads: HashMap<(Site, String), (Sender<BlenderResult>, Receiver<BlenderResult>)>,
    }

    use rocket::request::State;
    use std::sync::RwLock;
    /// Retrieve a blend file or wait if not computed yet
    #[get("/get/<site>/<game_id>")]
    fn get(site: Site, game_id: String, state: State<RwLock<WebappState>>) -> Result<Template, Template> {
        match simulation_status(&site, game_id.clone(), state) {
            SimulationStatus::Finished => {
                use std::collections::HashMap;

                let blend_link = format!("{}/{:?}_{}.blend", BLEND_FILES_URL_PREFIX, &site, &game_id);

                let mut context = HashMap::new();
                context.insert("blend_link", blend_link);

                Ok(Template::render("download", &context))
            },
            SimulationStatus::NotRunning => {
                let mut context = HashMap::new();
                context.insert("error_message", "Can't find this ID... maybe re-try?");
                Err(Template::render("error", &context))
            },
            SimulationStatus::Running => {
                let mut context = HashMap::new();
                context.insert("", "");
                Ok(Template::render("refresh", &context))
            },
            SimulationStatus::Failed => {
                let mut context = HashMap::new();
                context.insert("error_message", "Simulation failed");
                Err(Template::render("error", &context))
            },
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
        let webapp_state = WebappState {
            stats: WebappStats { total_runs: 0, current_running: 0 },
            threads: HashMap::new(),
        };
        
        rocket::custom(config, true)
            .mount("/webapp", routes![index, get, post])
            .mount("/monitoring", routes![stats])
            .attach(Template::fairing())
            .manage(RwLock::new(webapp_state))
    }

    pub fn run() {
        rocket_chess()
            .launch();
    }
}  // end fracture_chess

fn main() {
    fracture_chess::run();
}


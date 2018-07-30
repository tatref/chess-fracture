#![feature(plugin)]
#![plugin(rocket_codegen)]
#![feature(custom_derive)] 

extern crate rocket;
extern crate rocket_contrib;
#[macro_use] extern crate serde_derive;
extern crate shiplift;
extern crate url;
extern crate regex;
extern crate reqwest;
#[cfg(test)] #[macro_use] extern crate lazy_static;



mod test;


mod fracture_chess {
    //use rocket::Request;
    //use rocket::http::Cookies;
    use regex::Regex;
    use rocket::request::Form;
    use rocket::request::FormItems;
    use rocket::request::FromForm;
    use rocket::response::Redirect;
    use rocket;
    use rocket_contrib::Template;
    use url::Url;
    use reqwest;
    use rocket::http::RawStr;

    
    #[get("/")]
    fn index() -> Template {
        use std::collections::HashMap;
        let mut context = HashMap::new();
        context.insert(0, 0);

        Template::render("index", &context)
    }

    #[derive(Clone, Debug)]
    enum Site {
        Lichess,
    }

    impl<'a> rocket::request::FromParam<'a> for Site {
        type Error = ();

        fn from_param(param: &'a RawStr) -> Result<Self, Self::Error> {
            match param.as_str() {
                "lichess" => Ok(Site::Lichess),
                _ => Err(()),
            }
        }
    }
    
    
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
                let mut pgn_name = String::from(game_id);
                pgn_name.push_str(".pgn");
    
                let base_url = Url::parse("https://lichess.org/game/export/")
                    .unwrap();  // always succeeds
                let pgn_url = base_url.join(&pgn_name).unwrap();

                return Ok( PgnUrl { site: Site::Lichess, pgn_url, game_id: game_id.into() });
            },
            Some(_) => Err(()),
            _ => Err(()),
        }
    }

    #[derive(Clone, Debug)]
    struct PgnUrl {
        site: Site,
        pgn_url: Url,  // TODO: not required
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
    
    #[post("/post", format = "application/x-www-form-urlencoded", data = "<pgnurl>")]
    fn post(pgnurl: Form<PgnUrl>) -> Result<Redirect, String> {
        let PgnUrl { site, pgn_url, game_id } = pgnurl.into_inner();

        let pgn = reqwest::get(pgn_url)
            .unwrap()
            .text()
            .unwrap();
        if pgn == "Can't export PGN of game in progress" {
            return Err("Can't export PGN of game in progress".into())
        }

        let site_str: &str = match site {
            Lichess => "lichess".into(),
            _ => unimplemented!(),
        };

        let redirect_url = format!("/get/{}/{}", site_str, game_id);
        Ok(Redirect::to(&redirect_url))
    }

    /// Retrieve a blend file or wait if not computed yet
    #[get("/get/<site>/<game_id>")]
    fn get(site: Site, game_id: String) -> String {
        game_id.to_string()
    }

    pub fn rocket_chess() -> rocket::Rocket {
        rocket::ignite()
            .mount("/", routes![index, get, post])
            .attach(Template::fairing())
    }

    pub fn run() {
        rocket_chess()
            .launch();
    }
}

fn main() {
    fracture_chess::run();

    use std::process::Command;
    use std::collections::HashMap;


    enum MountType {
        Bind,
        Volume,
        Tmpfs,
    }

    struct Mount {
        mount_type: MountType,
        src: String,
        dst: String,
        ro: bool,
    }
    impl Mount {
        fn new(mount_type: MountType, src: String, dst: String, ro: bool) -> Self {
            Mount { mount_type, src, dst, ro }
        }
    }

    impl std::fmt::Display for Mount {
        fn fmt(&self, f: &mut std::fmt::Formatter) -> std::fmt::Result {
            write!(f, "--mount type=")?;
            match self.mount_type {
                MountType::Bind => write!(f, "bind,"),
                MountType::Volume => write!(f, "mount,"),
                MountType::Tmpfs => write!(f, "tmpfs,"),
            }?;
            if self.ro {
                write!(f, "ro=true,")?;
            }
            write!(f, "src={},", self.src)?;
            write!(f, "dst={}", self.dst)?;
            Ok(())
        }
    }
    
    fn docker_run(image_name: &str,
            container_name: &str,
            env: &HashMap<String, String>,
            mounts: &Vec<Mount>,
            ) {
        let mut args: Vec<String> = vec![
            "run".into(),
            "--name".into(),
            container_name.into(),
            "--security-opt".into(),
            "label=type:container_runtime_t".into(),
            "--rm".into(),
        ];

        for (k, v) in env.iter() {
            args.push("-e".into());
            args.push(format!("{}={}", k, v));
        }

        for mount in mounts.iter() {
            args.push(format!("{}", mount));
        }


        args.push(image_name.into());
        println!("{:?}", args);
        return;

        let child = Command::new("docker")
            .args(&args)
            .spawn()
            .expect("failed to execute docker");

        let output = child
            .wait_with_output()
            .unwrap();
        println!("{:?}", output);
    }

    let x_display = String::from("1");

    let mut env = HashMap::new();
    env.insert("DISPLAY".into(), format!(":{}", x_display));
    env.insert("PGN_NAME".into(), "best_game.blend".into());

    let mut mounts = Vec::new();
    mounts.push(Mount::new(MountType::Bind, "../blender/o4qX1cyD.pgn".into(), "/work/input.pgn".into(), true));
    mounts.push(Mount::new(MountType::Volume, "blend_files".into(), "/output".into(), false));
    mounts.push(Mount::new(MountType::Bind, format!("/tmp/.X11-unix/X{}", x_display.clone()), format!("/tmp/.X11-unix/X{}", x_display.clone()), false));

    

    docker_run("centos", "mycontainer", &env, &mounts);



}

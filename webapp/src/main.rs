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
    use shiplift;
    use reqwest;


    #[derive(Serialize)]
    struct TemplateContext {
        name: String,
        items: Vec<String>
    }
    
    #[derive(Serialize)]
    struct ContainersListContext {
        containers: Vec<shiplift::rep::Container>,
    }
    
    #[get("/containers")]
    fn containers() -> Template {
        let context = ContainersListContext {
            containers: Vec::new(),
        };
    
        Template::render("containers", &context)
    }
    
    #[get("/")]
    fn index() -> Redirect {
        Redirect::permanent("/containers")
    }
    
    
    
    #[get("/hello/<name>")]
    fn get(name: String) -> Template {
        let context = TemplateContext {
            name: name,
            items: vec!["One", "Two", "Three"].iter().map(|s| s.to_string()).collect()
        };
    
        Template::render("index", &context)
    }
    
    fn get_pgn_download_url(url: &Url) -> Result<Url, ()> {
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
                let pgn_link = base_url.join(&pgn_name).unwrap();
                return Ok(pgn_link);
            },
            Some(_) => Err(()),
            _ => Err(()),
        }
    }
    
    struct PgnUrl {
        pgn_url: Url,
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
    
                        return get_pgn_download_url(&url)
                            .map(|url| PgnUrl { pgn_url: url })
                    },
                    _ if strict => return Err(()),
                    _ => { /* allow extra value when not strict */ }
                }
            }
    
            return Err(())
        }
    }
    
    #[post("/pgnurl", format = "application/x-www-form-urlencoded", data = "<url>")]
    fn pgnurl(url: Form<PgnUrl>) -> Result<String, String> {
        let pgn_url = url.into_inner().pgn_url;
        let pgn = reqwest::get(pgn_url)
            .unwrap()
            .text()
            .unwrap();
        if pgn == "Can't export PGN of game in progress" {
            Err("Can't export PGN of game in progress".into())
        }
        else {
            Ok("foo".into())
        }
    }

    pub fn rocket_chess() -> rocket::Rocket {
        rocket::ignite()
            .mount("/", routes![index, get, containers, pgnurl])
            .attach(Template::fairing())
    }

    pub fn run() {
        rocket_chess()
            .launch();
    }
}

fn main() {
    //fracture_chess::run();
    //let docker = shiplift::Docker::new().unwrap();
    //let containers = docker.containers();
    ////let c = containers.get("ecstatic_chebyshe");
    ////println!("{:?}", c.inspect());

    //let container_options = shiplift::builder::ContainerOptionsBuilder::new("chess-fracture:latest")
    //    .name("myfracture")
    //    .build();
    //let res = containers.create(&container_options);
    //println!("{:?}", res);

    use std::process::Command;
    
    fn docker_run(image_name: &str, cmd: &[&str]) {
        let vnc_display = 1;
        let chess_fracture_pgn_path = "./././file.pgn";
        let pgn_name = "lichess_xxxx";

        let vol_pgn_path = format!("{}:/work/input.pgn:ro", chess_fracture_pgn_path);
        let vol_x11_socket = format!("/tmp/.X11-unix/X{}:/tmp/.X11-unix/X{}", vnc_display, vnc_display);
        let env_display = format!("DISPLAY=:{}", vnc_display);
        let env_pgn_name = format!("PGN_NAME={}", pgn_name);

        let container_name = format!("blender-fracture");



        let args = &["run",
                     "--name",
                     &container_name,
                     "--security-opt",
                     "label=type:container_runtime_t",
                     "--rm",
                     "-v",
                     &vol_pgn_path,
                     "-v",
                     "blend_files:/output",
                     "-v",
                     &vol_x11_socket,
                     "-e",
                     &env_display,
                     "-e",
                     &env_pgn_name,
                     "chess-fracture:latest"];

        let child = Command::new("docker")
            .args(args)
            .spawn()
            .expect("failed to execute docker");

        let output = child
            .wait_with_output()
            .unwrap();
        println!("{:?}", output);
    }

    docker_run("centos", &["ls", "-al"]);

}

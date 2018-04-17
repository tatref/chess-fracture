#![feature(plugin)]
#![plugin(rocket_codegen)]
#![feature(custom_derive)] 

extern crate rocket;
extern crate rocket_contrib;
#[macro_use] extern crate serde_derive;
extern crate shiplift;
extern crate url;
extern crate regex;





#[cfg(test)]
mod test {
    use rocket::local::Client;
    use rocket::http::Status;
    use fracture_chess;

    #[test]
    fn main_page() {
        let rocket = fracture_chess::rocket_chess();
        let client = Client::new(rocket).expect("valid rocket instance");

        let response = client.get("/").dispatch();
        assert_eq!(response.status(), Status::PermanentRedirect);
    }
}


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
    
    fn get_pgn_download_url(url: &Url) -> Option<Url> {
        match url.domain() {
            Some("lichess.org") => {
                // Game URL: https://lichess.org/xxxxx/white
                // PGN URL:  https://lichess.org/game/export/xxxx.pgn
                let re = Regex::new(r"^https://lichess.org/(?P<gameid>[[:alnum:]]+)(/(white|black)(#\d+)?)?$")
                    .unwrap();
                let game_id = re.captures(url.as_str())
                    .unwrap()  // TODO: handle error
                    .name("gameid")
                    .unwrap()  // always succeeds
                    .as_str();
                let mut pgn_name = String::from(game_id);
                pgn_name.push_str(".pgn");
    
                let base_url = Url::parse("https://lichess.org/game/export/")
                    .unwrap();  // always succeeds
                let pgn_link = base_url.join(&pgn_name).unwrap();
                return Some(pgn_link);
            },
            Some(_) => None,
            _ => None,
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
    
                        match get_pgn_download_url(&url) {
                            Some(url) => return Ok(PgnUrl {
                                    pgn_url: url,
                                }),
                            None => return Err(()),
                        }
                    },
                    _ if strict => return Err(()),
                    _ => { /* allow extra value when not strict */ }
                }
            }
    
            return Err(())
        }
    }
    
    #[post("/pgnurl", format = "application/x-www-form-urlencoded", data = "<url>")]
    fn pgnurl(url: Form<PgnUrl>) -> String {
        url.into_inner().pgn_url.as_str().into()
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
    //let docker = shiplift::Docker::new().unwrap();
    //let containers = docker.containers();
    //let c = containers.get("ecstatic_chebyshe");
    //println!("{:?}", c.inspect());

    //let container_options = shiplift::builder::ContainerOptionsBuilder::new("chess-fracture")
    //    .name("myfracture")
    //    .build();
    //let res = containers.create(&container_options);
    //println!("{:?}", res);
    
    fracture_chess::run();
}

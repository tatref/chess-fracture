#![feature(plugin)]
#![plugin(rocket_codegen)]

extern crate rocket;
extern crate rocket_contrib;
#[macro_use] extern crate serde_derive;
extern crate shiplift;



use rocket_contrib::Template;
use rocket::http::Cookies;
use rocket::Request;
use rocket::response::Redirect;



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
    Redirect::to("/containers")
}



#[get("/hello/<name>")]
fn get(name: String) -> Template {
    let context = TemplateContext {
        name: name,
        items: vec!["One", "Two", "Three"].iter().map(|s| s.to_string()).collect()
    };

    Template::render("index", &context)
}


#[post("/post")]
fn post() -> &'static str {
    "posted!"
}

fn main() {
    let docker = shiplift::Docker::new().unwrap();
    let containers = docker.containers();
    let c = containers.get("ecstatic_chebyshe");
    println!("{:?}", c.inspect());

    let containerOptions = shiplift::builder::ContainerOptionsBuilder::new("chess-fracture")
        .name("myfracture")
        .build();
    let res = containers.create(&containerOptions);
    println!("{:?}", res);
    

    rocket::ignite()
        .mount("/", routes![index, get, containers])
        .attach(Template::fairing())
        .launch();
}

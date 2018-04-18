
#[cfg(test)]
mod test {
    use rocket::local::Client;
    use rocket::http::Status;
    use fracture_chess;

    lazy_static! {
        static ref CLIENT: Client = {
            let rocket = fracture_chess::rocket_chess();
            Client::new(rocket).expect("valid rocket instance")
        };
    }

    #[test]
    fn main_page() {
        let response = CLIENT.get("/").dispatch();
        assert_eq!(response.status(), Status::PermanentRedirect);
    }

    #[test]
    fn main_page() {
        let response = CLIENT.get("/").dispatch();
        assert_eq!(response.status(), Status::PermanentRedirect);
    }
}

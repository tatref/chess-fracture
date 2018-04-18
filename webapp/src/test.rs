
#[cfg(test)]
mod test {
    use rocket::local::Client;
    use rocket::http::Status;
    use rocket::http::ContentType;
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
    fn lichess_png1() {
        let response = CLIENT
            .post("/pgnurl")
            .body("url=https://lichess.org/Cvjr6hwJ")
            .header(ContentType::Form)
            .dispatch();
        assert_eq!(response.status(), Status::Ok)
    }
    #[test]
    fn lichess_png2() {
        let response = CLIENT
            .post("/pgnurl")
            .body("url=https://lichess.org/Cvjr6hwJ")
            .header(ContentType::Form)
            .dispatch();
        assert_eq!(response.status(), Status::Ok)
    }
    #[test]
    fn lichess_png3() {
        let response = CLIENT
            .post("/pgnurl")
            .body("url=https://lichess.org/Cvjr6hwJ/white")
            .header(ContentType::Form)
            .dispatch();
        assert_eq!(response.status(), Status::Ok)
    }
    #[test]
    fn lichess_png4() {
        let response = CLIENT
            .post("/pgnurl")
            .body("url=https://lichess.org/Cvjr6hwJ/black#1")
            .header(ContentType::Form)
            .dispatch();
        assert_eq!(response.status(), Status::Ok)
    }
}

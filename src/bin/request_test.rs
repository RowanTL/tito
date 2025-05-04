use dotenv::dotenv;
use std::env;
use std::io::Read;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    dotenv().ok();

    let client = reqwest::blocking::Client::new();
    let mut res = client
        .get("https://paper-api.alpaca.markets/v2/account")
        .header("APCA-API-KEY-ID", env::var("APCA-API-KEY-ID")?)
        .header("APCA-API-SECRET-KEY", env::var("APCA-API-SECRET-KEY")?)
        .send()?;
    let mut body = String::new();
    res.read_to_string(&mut body)?;

    println!("Status: {}", res.status());
    println!("Headers:\n{:#?}", res.headers());
    println!("Body:\n{}", body);

    Ok(())
}

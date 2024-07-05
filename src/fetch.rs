use reqwest::{Client, StatusCode};
use serde::{Deserialize, Serialize};
use chrono::NaiveDate;
use dotenv::dotenv;
use std::env;
use thiserror::Error;

#[derive(Debug, Serialize, Deserialize)]
struct MonthlySalesResponse {
    #[serde(flatten)]
    sales: std::collections::HashMap<String, Vec<StoreSales>>,
}

#[derive(Debug, Serialize, Deserialize)]
struct StoreSales {
    store_id: String,
    sales: Vec<ProductSales>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ProductSales {
    product_id: String,
    sales_volume: f64,
    sales_quantity: i32,
    last_changed: LastChanged,
}

#[derive(Debug, Serialize, Deserialize)]
struct LastChanged {
    date: String,
    time: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct ProductDetailsResponse {
    #[serde(flatten)]
    details: std::collections::HashMap<String, ProductDetails>,
}

#[derive(Debug, Serialize, Deserialize)]
struct ProductDetails {
    basic: BasicDetails,
    last_changed: LastChanged,
}

#[derive(Debug, Serialize, Deserialize)]
struct BasicDetails {
    product_id: String,
    product_short_name: String,
}

#[derive(Debug, Serialize, Deserialize)]
struct PriceConditionsResponse {
    #[serde(flatten)]
    conditions: std::collections::HashMap<String, PriceConditions>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PriceConditions {
    price_elements: Vec<PriceElement>,
}

#[derive(Debug, Serialize, Deserialize)]
struct PriceElement {
    sales_price: f64,
    markup: f64,
    ddu_price: f64,
    sales_price_pr_liter: f64,
    value_added_tax: f64,
    alcohol_tax: f64,
    eco_tax: f64,
    packaging_tax: f64,
    bottle_return_value: f64,
}

#[derive(Error, Debug)]
enum VinmonopoletError {
    #[error("HTTP request failed: {0}")]
    RequestFailed(#[from] reqwest::Error),
    #[error("Resource not found")]
    NotFound,
    #[error("Unauthorized")]
    Unauthorized,
    #[error("Server error")]
    ServerError,
    #[error("Unknown error: {0}")]
    Unknown(String),
}

struct VinmonopoletClient {
    client: Client,
    base_url: String,
    api_key: String,
}

impl VinmonopoletClient {
    fn new() -> Result<Self, Box<dyn std::error::Error>> {
        dotenv().ok();
        let api_key = env::var("VINMONOPOLET_API_KEY").expect("VINMONOPOLET_API_KEY not found");
        let client = Client::new();
        let base_url = "https://apis.vinmonopolet.no/products/v0".to_string();

        Ok(Self {
            client,
            base_url,
            api_key,
        })
    }

    async fn get_monthly_sales(&self, from_sales_month: &str, to_sales_month: &str) -> Result<MonthlySalesResponse, VinmonopoletError> {
        let url = format!("{}/monthly-sales-per-store", self.base_url);
        let response = self.client.get(&url)
            .query(&[
                ("fromSalesMonth", from_sales_month),
                ("toSalesMonth", to_sales_month),
            ])
            .header("Ocp-Apim-Subscription-Key", &self.api_key)
            .send()
            .await?;

        self.handle_response(response).await
    }

    async fn get_product_details(&self, product_id: &str) -> Result<ProductDetailsResponse, VinmonopoletError> {
        let url = format!("{}/details-normal", self.base_url);
        let response = self.client.get(&url)
            .query(&[("productId", product_id)])
            .header("Ocp-Apim-Subscription-Key", &self.api_key)
            .send()
            .await?;

        self.handle_response(response).await
    }

    async fn get_price_conditions(&self, product_id: &str) -> Result<PriceConditionsResponse, VinmonopoletError> {
        let url = format!("{}/price-conditions", self.base_url);
        let response = self.client.get(&url)
            .query(&[("productId", product_id)])
            .header("Ocp-Apim-Subscription-Key", &self.api_key)
            .send()
            .await?;

        self.handle_response(response).await
    }

    async fn get_updated_products(&self, changed_since: NaiveDate) -> Result<ProductDetailsResponse, VinmonopoletError> {
        let url = format!("{}/details-normal", self.base_url);
        let response = self.client.get(&url)
            .query(&[("changedSince", changed_since.format("%Y-%m-%d").to_string())])
            .header("Ocp-Apim-Subscription-Key", &self.api_key)
            .send()
            .await?;

        self.handle_response(response).await
    }

    async fn handle_response<T: for<'de> Deserialize<'de>>(&self, response: reqwest::Response) -> Result<T, VinmonopoletError> {
        match response.status() {
            StatusCode::OK => Ok(response.json().await?),
            StatusCode::NOT_FOUND => Err(VinmonopoletError::NotFound),
            StatusCode::UNAUTHORIZED => Err(VinmonopoletError::Unauthorized),
            StatusCode::INTERNAL_SERVER_ERROR => Err(VinmonopoletError::ServerError),
            _ => Err(VinmonopoletError::Unknown(format!("Unexpected status code: {}", response.status()))),
        }
    }
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let client = VinmonopoletClient::new()?;
    let args: Vec<String> = env::args().collect();

    if args.len() < 2 {
        println!("Usage:");
        println!("  cargo run -- monthly-sales <from_date> <to_date>");
        println!("  cargo run -- product-details <product_id>");
        println!("  cargo run -- price-conditions <product_id>");
        println!("  cargo run -- updated-products <since_date>");
        return Ok(());
    }

    match args[1].as_str() {
        "monthly-sales" => {
            if args.len() < 4 {
                println!("Please provide from_date and to_date for monthly sales");
                return Ok(());
            }
            match client.get_monthly_sales(&args[2], &args[3]).await {
                Ok(monthly_sales) => println!("Monthly sales: {:?}", monthly_sales),
                Err(e) => println!("Error fetching monthly sales: {:?}", e),
            }
        }
        "product-details" => {
            if args.len() < 3 {
                println!("Please provide a product_id for product details");
                return Ok(());
            }
            match client.get_product_details(&args[2]).await {
                Ok(product_details) => println!("Product details: {:?}", product_details),
                Err(e) => println!("Error fetching product details: {:?}", e),
            }
        }
        "price-conditions" => {
            if args.len() < 3 {
                println!("Please provide a product_id for price conditions");
                return Ok(());
            }
            match client.get_price_conditions(&args[2]).await {
                Ok(price_conditions) => println!("Price conditions: {:?}", price_conditions),
                Err(e) => println!("Error fetching price conditions: {:?}", e),
            }
        }
        "updated-products" => {
            if args.len() < 3 {
                println!("Please provide a since_date for updated products");
                return Ok(());
            }
            let since_date = NaiveDate::parse_from_str(&args[2], "%Y-%m-%d")?;
            match client.get_updated_products(since_date).await {
                Ok(updated_products) => println!("Updated products: {:?}", updated_products),
                Err(e) => println!("Error fetching updated products: {:?}", e),
            }
        }
        _ => {
            println!("Unknown command. Use one of: monthly-sales, product-details, price-conditions, updated-products");
        }
    }

    Ok(())
}
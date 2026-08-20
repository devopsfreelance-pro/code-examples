use anyhow::Result;
use spin_sdk::http::{IntoResponse, Request, Response};
use spin_sdk::http_component;

/// Componente HTTP compilado a WebAssembly (target wasm32-wasip1) y servido
/// por el runtime de Spin. Ilustra el ejemplo de código del post: un handler
/// mínimo que responde a peticiones HTTP con arranque en frío de milisegundos.
#[http_component]
fn handle_request(req: Request) -> Result<impl IntoResponse> {
    let path = req.header("spin-path-info");

    let body = format!(
        r#"{{"status":"healthy","runtime":"wasm","path":"{}"}}"#,
        path.and_then(|v| v.as_str()).unwrap_or("/")
    );

    Ok(Response::builder()
        .status(200)
        .header("content-type", "application/json")
        .body(body)
        .build())
}

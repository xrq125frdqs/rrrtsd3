
from fastapi import FastAPI, Request,Form
from fastapi.responses import JSONResponse, HTMLResponse
from helpers.proxy_checker import process_proxy 
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader



app = FastAPI()

env = Environment(loader=FileSystemLoader("templates"))

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request):
    template = env.get_template("index.html")
    return template.render()

@app.get("/api/v1")
async def check_proxy_url_endpoint(request: Request):
    ip_address = request.query_params.get("ip")
    port_number = request.query_params.get("port")

    if not ip_address or not port_number:
        return JSONResponse(status_code=400, content={"error": "Parameter 'ip' dan 'port' harus diberikan dalam URL. fomat harus /?ip=192.168.1.1&port=80"})

    try:
        result = process_proxy(ip_address, port_number) # Panggil process_proxy yang diimport
        proxyip, message, country_code, asn, country_name, country_flag, http_protocol, org_name, connection_time = result

        if proxyip:
            response_data = {
                "ip": ip_address,
                "port": port_number,
                "proxyip": True,
                "asOrganization": org_name,
                "countryCode": country_code,
                "countryName": country_name,
                "countryFlag": country_flag,
                "asn": asn,
                "message": message,
                "httpProtocol": http_protocol,
                "delay": f"{round(connection_time)} ms"
            }
        else:
            response_data = {
                "ip": ip_address,
                "port": port_number,
                "proxyip": False,
                "asn": asn,
                "message": message
            }

        return response_data

    except Exception as e:
        error_message = f"Terjadi kesalahan server saat memproses proxy {ip_address}:{port_number}: {e}"
        print(error_message)
        return JSONResponse(status_code=500, content={"error": error_message})
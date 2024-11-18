# fp-traefik

`fp-traefik` is a [frps](https://github.com/fatedier/frp) plugin
that enables the use of frp as a configuration discovery source for [Traefik](https://traefik.io/traefik/).

As an [HTTP plugin](https://github.com/fatedier/frp/blob/master/doc/server_plugin.md) for frps,
`fp-traefik` will receive HTTP requests from frps when a frpc client connects to frps,
and set key-value pairs to Redis based on requests.
Traefik that connected to the same Redis server,
updates its dynamic configuration accordingly upon detecting changes in the key-value pairs.

## Usage

1. **Clone the repository and install dependencies**

   ```shell
   git clone https://github.com/Chihsiao/fp-traefik.git && cd fp-traefik
   poetry install
   ```

2. **Configure environment variables**

   The configuration for `fp-traefik` is set through environment variables, which are listed below:

   - `FP_TRAEFIK_REDIS_URL`: Redis connection URL.
   - `FP_TRAEFIK_SUBDOMAIN_HOST`: Corresponds to the `subdomainHost` in frps.
   - `FP_TRAEFIK_DEFAULT_SERVICE`: Default service when no service is set for routers.
   - `FP_TRAEFIK_DEFAULT_ENTRYPOINT`: Default entry point when no entry point is set for routers.
   - `FP_TRAEFIK_DEFAULT_ROUTER_NAME_PREFIX`: Prefix used for the default router name when no router is set for proxies.
   - `FP_TRAEFIK_VERBOSE`: Controls the logging level; setting it to `true` enables debug mode.

   - `FP_TRAEFIK_EXPOSED_BY_DEFAULT`: Whether to autoconfigure proxies.
     - Can be overridden by `metadatas."traefik/enable"` in the frpc configuration.

3. **Run the application**

   ```shell
   poetry run waitress fp_traefik.app:app
   ```

4. **Integrate with frps and Traefik**

   1. _Configure frps_

      Add the following configuration to the frps configuration file:

      ```toml
      [[httpPlugins]]
      name = "fp_traefik"
      addr = "i_am_the_address_to_fp_traefik:8080"
      path = "/handler"
      ops = [
         "NewProxy",
         "CloseProxy",
         "NewWorkConn",
      ]
      ```

   2. _Configure Traefik_

      Use the same Redis instance as the configuration source for `fp-traefik`, refer to [Traefik & Redis](https://doc.traefik.io/traefik/providers/redis/) for more details.

5. **Set up frpc**

   Below is an example of a possible frpc configuration:

   ```toml
   serverAddr = "frps"
   serverPort = 7000
   
   [[proxies]]
   name = "whoami"
   localIP = "127.0.0.1"
   localPort = 80
   type = "http"
   subdomain = "www"
   locations = ["/foo", "/bar"]
   ```

   This will set the following key-value pairs in Redis:

   ```redis
   SET "traefik/http/routesr/frp-whoami/service" "frp"
   SET "traefik/http/routers/frp-whoami/entryPoints/0" "web"
   SET "traefik/http/routers/frp-whoami/rule" "Host(`www.example.org`) && (PathPrefix(`/foo`) || PathPrefix(`/bar`))"
   ```

   Currently, it only supports generating Traefik configurations for proxies whose type is `http`.
   However, you can use `metadatas` to set custom Traefik configurations, supporting any type of proxy, for example:

   ```toml
   serverAddr = "frps"
   serverPort = 7000
   # ...
   [metadatas]  # connection-level configuration
   "traefik/http/middlewares/enable-compression/compress" = "true"
   
   [[proxies]]
   # ...
   [proxies.metadatas]  # proxy-level configuration
   "traefik/http/routers/frp-whoami/middlewares/0" = "enable-compression"
   "traefik/http/routers/frp-whoami/entryPoints/0" = "web-secure"
   "traefik/http/routers/frp-whoami/tls" = "true"
   ```

   Connection-level metadata applies to the entire connection, while proxy-level metadata only affects the specific proxy.

The [compose.yml](compose.yml) provides a simple example to run `fp-traefik` along with frps and Traefik.

## License

This project is licensed under the MIT License. For more details, see the [LICENSE](LICENSE) file.

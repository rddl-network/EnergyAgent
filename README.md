# RDDL EnergyAgent

The EnergyAgent service connects an MQTT service (locally or self-defined) to connect SMDs and notarizes the data of the SMDs (connected via MQTT) to the RDDL network.

Tasmota- and Shelly-compatible devices are currently supported types of SMDs. More can be added upon request (preferably PRs on Git Hub).

The RDDL network identity and the needed key material are managed by the attached TrustWallet.
The RDDL network configuration (mainnet or testnet) can be set via the UI or the command line.

But there is more to be configured! The following set of environment variables can be defined:

```
LOG_LEVEL =          "INFO"                # the log level
CONFIG_PATH =        "/tmp"                # the basic config folder where
                                           #   mqtt_config.json, 
                                           #   smart_meter_config.json, and 
                                           #   energy_agent.db are expected
RDDL_TOPIC =         "rddl/SMD/#""         # the channel to subscribe to SMD data updates
TRUST_WALLET_PORT =  "/dev/ttyACM0"        # the serial devices port to the TrustWallet
NOTARIZE_INTERVAL =  3600                  # in seconds 3600 seconds = 1 hour
CLIENT_ID =          energy_agent
RDDL_NETWORK_MODE =  testnet               # testnet, mainnet, or custom
```

The custom RDDL network connection can be set via the following environment variables:

```
CHAIN_ID =           "planetmintgo"
PLANETMINT_API =     "http://localhost:1317"
TA_BASE_URL =        "http://localhost:8080"
RDDL_MQTT_USER =     "user"
RDDL_MQTT_PASSWORD = "pwd"
RDDL_MQTT_SERVER =   "localhost"
RDDL_MQTT_PORT =     "1883"
```

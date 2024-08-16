import json
import requests
from typing import Tuple, List
from app.dependencies import config
from app.dependencies import trust_wallet_instance
from app.helpers.models import PoPContext
from app.helpers.logs import log, logger


@log
def createAccountOnNetwork(
    ta_service_base_url: str, machineId: str, plmnt_address: str, signature: str
) -> requests.Response:
    # Define the URL and data
    url = ta_service_base_url + "/create-account"
    data = {"machine-id": machineId, "plmnt-address": plmnt_address, "signature": signature}

    # Set headers
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.post(url, json=data, headers=headers)
    return response


@log
def getAccountInfo(apiURL: str, address: str) -> Tuple[int, int, str]:
    queryURL = apiURL + "/cosmos/auth/v1beta1/account_info/" + address
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.get(queryURL, headers=headers)

    accountID = 0
    sequence = 0
    statusMsg = ""
    if response.status_code != 200:
        statusMsg = response.text
    else:
        data = json.loads(response.text)
        accountID = int(data["info"]["account_number"])
        sequence = int(data["info"]["sequence"])
        statusMsg = ""

    return (accountID, sequence, statusMsg)


@log
def getMachineInfo(apiURL: str, address: str) -> Tuple[str, str]:
    queryURL = apiURL + "/planetmint/machine/address/" + address
    headers = {"Content-Type": "application/json"}

    # Send POST request with JSON data and headers
    response = requests.get(queryURL, headers=headers)

    machinedata = ""
    statusMsg = ""
    if response.status_code != 200:
        statusMsg = response.text
    else:
        machinedata = json.loads(response.text)
        statusMsg = ""

    return (machinedata, statusMsg)


@log
def getBalance(address: str) -> dict:
    url = f"{config.rddl.planetmint_api}/cosmos/bank/v1beta1/balances/{address}"
    headers = {"Content-Type": "application/json"}

    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Failed to get balance: {response.text}")

    data = json.loads(response.text)
    balance = data["balances"]
    return balance


@log
async def queryNotatizedAssets(challengee: str, num_cids: int) -> List[str]:
    # Define the API endpoint URL
    url = config.rddl.planetmint_api + "/planetmint/asset/address/" + challengee + "/" + str(num_cids)
    # Set the header for accepting JSON data
    headers = {"accept": "application/json"}

    # Send a GET request using requests library
    response = requests.get(url, headers=headers)

    # Check for successful response status code
    if response.status_code == 200:
        # Parse the JSON response (assuming successful status code)
        try:
            data = json.loads(response.text)

            # Verify "challenge" key exists and all desired keys are present
            if "cids" in data:
                return data["cids"]
            else:
                logger.error("Error: Missing key(s) in response.")
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON response.")
    else:
        logger.error("Error:    " + str(response.status_code))
    return None


@log
async def queryPoPInfo(height: str) -> PoPContext:
    # Define the API endpoint URL
    url = config.rddl.planetmint_api + "/planetmint/dao/challenge/" + height
    # Set the header for accepting JSON data
    headers = {"accept": "application/json"}

    # Send a GET request using requests library
    response = requests.get(url, headers=headers)

    # Check for successful response status code
    if response.status_code == 200:
        # Parse the JSON response (assuming successful status code)
        try:
            data = json.loads(response.text)

            # Verify "challenge" key exists and all desired keys are present
            if "challenge" in data and all(
                key in data["challenge"]
                for key in ["initiator", "challenger", "challengee", "height", "success", "finished"]
            ):
                # Access and print the challenge variables
                if (
                    data["challenge"]["height"] == height
                    and not data["challenge"]["success"]
                    and not data["challenge"]["finished"]
                ):
                    pop_context = PoPContext()

                    keys = trust_wallet_instance.get_planetmint_keys()
                    pop_context.initiator = data["challenge"]["initiator"]
                    pop_context.challenger = data["challenge"]["challenger"]
                    pop_context.challengee = data["challenge"]["challengee"]
                    pop_context.pop_height = 0
                    pop_context.isChallenger = pop_context.challenger == keys.planetmint_address
                    try:
                        pop_context.pop_height = int(data["challenge"]["height"])
                    except Exception as e:
                        logger.error("Error: cannot convert string to int (pop height): " + str(e))
                    if pop_context.isChallenger or (pop_context.challengee == keys.planetmint_address):
                        pop_context.isActive = True
                        return pop_context
            else:
                logger.error("Error: Missing key(s) in response.")
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON response.")
    else:
        logger.error("Error: " + str(response.status_code))
    return PoPContext()

import json
import requests
from typing import Tuple, List
from app.dependencies import config, logger
from app.dependencies import trust_wallet_instance


async def queryNotatizedAssets(challengee: str, num_cids: int) -> List[str]:
    # Define the API endpoint URL
    url = config.planetmint_api + "/planetmint/dao/challenge/" + challengee + "/" + str(num_cids)
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


async def queryPoPInfo(height: str) -> Tuple[str, str, str, int, bool, bool]:
    # Define the API endpoint URL
    url = config.planetmint_api + "/planetmint/dao/challenge/" + height
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
                logger.info("Initiator: " + data["challenge"]["initiator"])
                logger.info("Challenger: " + data["challenge"]["challenger"])
                logger.info("Challengee: " + data["challenge"]["challengee"])
                logger.info("Height: " + data["challenge"]["height"])
                logger.info("Success: " + str(data["challenge"]["success"]))
                logger.info("Finished: " + str(data["challenge"]["finished"]))
                if (
                    data["challenge"]["height"] == height
                    and data["challenge"]["success"] == False
                    and data["challenge"]["finished"] == False
                ):

                    keys = keys = trust_wallet_instance.get_planetmint_keys()
                    initiator = data["challenge"]["initiator"]
                    challenger = data["challenge"]["challenger"]
                    challengee = data["challenge"]["challengee"]
                    isChallenger = challenger == keys.planetmint_address
                    pop_height = 0
                    try:
                        pop_height = int(data["challenge"]["height"])
                    except: 
                        logger.error("Erro: cannot convert string to int (pop height)")
                    if isChallenger or challengee == keys.planetmint_address:
                        return (initiator, challenger, challengee, pop_height, isChallenger, True)
            else:
                logger.error("Error: Missing key(s) in response.")
        except json.JSONDecodeError:
            logger.error("Error: Invalid JSON response.")
    else:
        logger.error("Error: "+ str(response.status_code))
    return ("", "", "", 0, False, False)

from abc import ABC, abstractmethod
from typing import Tuple

from app.helpers.models import PlanetMintKeys


class ITrustWalletConnector(ABC):
    @abstractmethod
    def create_mnemonic(self) -> str:
        pass

    @abstractmethod
    def recover_from_mnemonic(self, mnemonic: str) -> str:
        pass

    @abstractmethod
    def get_planetmint_keys(self) -> PlanetMintKeys:
        pass

    @abstractmethod
    def sign_hash_with_planetmint(self, data_to_sign: str) -> str:
        pass

    @abstractmethod
    def sign_hash_with_rddl(self, data_to_sign: str) -> str:
        pass

    @abstractmethod
    def create_keypair_nist(self, ctx: int) -> str:
        pass

    @abstractmethod
    def get_machine_id(self, ctx: int) -> str:
        pass

    @abstractmethod
    def sign_with_nist(self, data_to_sign: str, ctx: int) -> str:
        pass

    @abstractmethod
    def verify_nist_signature(self, data_to_sign: str, signature: str, ctx: int) -> bool:
        pass

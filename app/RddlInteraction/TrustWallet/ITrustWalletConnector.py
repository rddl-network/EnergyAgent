from abc import ABC, abstractmethod
from typing import Tuple

from app.helpers.models import PlanetMintKeys


class ITrustWalletConnector(ABC):
    @abstractmethod
    def valise_get(self) -> str:
        pass

    @abstractmethod
    def create_mnemonic(self) -> str:
        pass

    @abstractmethod
    def inject_planetmintkey_to_se050(self, slot: int) -> bool:
        pass

    @abstractmethod
    def recover_from_mnemonic(self, mnemonic: str) -> str:
        pass

    @abstractmethod
    def get_planetmint_keys(self) -> PlanetMintKeys:
        pass

    @abstractmethod
    def get_seed_se050(self):
        pass

    @abstractmethod
    def sign_hash_with_planetmint(self, data_to_sign: str) -> str:
        pass

    @abstractmethod
    def sign_hash_with_rddl(self, data_to_sign: str) -> str:
        pass

    @abstractmethod
    def create_optega_keypair(self, ctx: int) -> str:
        pass

    @abstractmethod
    def sign_with_optega(self, ctx: int, data_to_sign: str, pubkey: str) -> str:
        pass

    @abstractmethod
    def unwrapPublicKey(self, public_key: str) -> Tuple[bool, str]:
        pass

    @abstractmethod
    def calculate_hash(self, data_to_sign: str) -> str:
        pass

    @abstractmethod
    def create_se050_keypair_nist(self, ctx: int) -> str:
        pass

    @abstractmethod
    def get_public_key_from_se050(self, ctx: int) -> str:
        pass

    @abstractmethod
    def sign_with_se050(self, data_to_sign: str, ctx: int) -> str:
        pass

    @abstractmethod
    def verify_se050_signature(self, data_to_sign: str, signature: str, ctx: int) -> bool:
        pass

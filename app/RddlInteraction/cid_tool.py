from ipfs_cid import cid_sha256_hash

from app.db.cid_store import insert_key_value


def store_cid(data: str) -> str:
    cid = cid_sha256_hash(data.encode("utf-8"))
    insert_key_value(cid, data)
    return cid

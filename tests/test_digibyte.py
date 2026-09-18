import asyncio
import tempfile

from electrum import constants
from electrum import bitcoin
from electrum import keystore
from electrum import SimpleConfig
from electrum import util
from electrum.wallet import Standard_Wallet
from electrum.wallet_db import WalletDB
from electrum.network import parse_servers
from electrum.digibyte_difficulty import POW_LIMIT, next_bits, target_to_bits
from electrum.digibyte_pow import pow_hash, pow_hash_batch



def test_digibyte_mainnet_parameters():
    net = constants.DigiByteMainnet

    assert net.NET_NAME == "digibyte"
    assert net.GENESIS == "7497ea1b465eb39f1c8f507bc877078fe016d6fcb6dfad3a64c98dcc6e1e8496"
    assert net.WIF_PREFIX == 0x80
    assert net.ADDRTYPE_P2PKH == 30
    assert net.ADDRTYPE_P2SH == 63
    assert net.SEGWIT_HRP == "dgb"
    assert net.BIP44_COIN_TYPE == 20
    assert net.DEFAULT_PORTS == {"t": "50011", "s": "50012"}


def test_posix_user_dir_is_digibyte_specific(monkeypatch):
    monkeypatch.delenv("ELECTRUMDIR", raising=False)
    monkeypatch.setenv("HOME", "/home/test-user")
    assert util.user_dir() == "/home/test-user/.electrum-digibyte"


def test_digibyte_address_formats(monkeypatch):
    monkeypatch.setattr(constants, "net", constants.DigiByteMainnet)
    pubkey = "0279be667ef9dcbbac55a06295ce870b07029bfcdb2dce28d959f2815b16f81798"

    p2pkh = bitcoin.pubkey_to_address("p2pkh", pubkey)
    assert p2pkh == "DFpN6QqFfUm3gKNaxN6tNcab1FArL9cZLE"
    assert bitcoin.address_to_script(p2pkh).hex() == "76a914751e76e8199196d454941c45d1b3a323f1433bd688ac"

    p2wpkh = bitcoin.pubkey_to_address("p2wpkh", pubkey)
    assert p2wpkh == "dgb1qw508d6qejxtdg4y5r3zarvary0c5xw7kmudfnm"
    witness_script = bitcoin.address_to_script(p2wpkh)
    assert witness_script.hex() == "0014751e76e8199196d454941c45d1b3a323f1433bd6"

    p2sh = bitcoin.redeem_script_to_address("p2sh", witness_script)
    assert p2sh == "SeXKCr4bJpNL9LTJcT7zbNZy9YK1Vihyox"
    assert bitcoin.is_address(p2pkh)
    assert bitcoin.is_address(p2sh)
    assert bitcoin.is_address(p2wpkh)


def test_digibyte_wif_and_bip44(monkeypatch):
    monkeypatch.setattr(constants, "net", constants.DigiByteMainnet)
    secret = bytes.fromhex("01" * 32)
    wif = bitcoin.serialize_privkey(secret, compressed=True, txin_type="p2pkh")

    assert wif == "p2pkh:KwFfNUhSDaASSAwtG7ssQM1uVX8RgX5GHWnnLfhfiQDigjioWXHH"
    assert bitcoin.deserialize_privkey(wif)[1:] == (secret, True)
    assert keystore.bip44_derivation(0) == "m/44h/20h/0h"


def test_digibyte_protocol_server_defaults(monkeypatch):
    monkeypatch.setattr(constants, "net", constants.DigiByteMainnet)
    parsed = parse_servers([['server.version', 'example.test', ['t']]])

    assert constants.DigiByteMainnet.DEFAULT_SERVERS == {}
    assert parsed['example.test']['t'] == '50011'


def test_digibyte_difficulty_uses_context_and_core_eras():
    def history(count, bits=target_to_bits(POW_LIMIT)):
        return [
            {'version': 0x0200 if height >= 145000 else 1,
             'timestamp': 1_000_000_000 + height * 15,
             'bits': bits}
            for height in range(count)
        ]

    # Before the first DigiShield retarget, the preceding block's bits apply.
    assert next_bits(history(1), {'version': 1, 'timestamp': 0, 'bits': 0}) == target_to_bits(POW_LIMIT)
    # The first DigiShield retarget is based on its 144-block window.
    headers = history(144)
    assert next_bits(headers, {'version': 1, 'timestamp': 0, 'bits': 0}) < target_to_bits(POW_LIMIT)

    # The rolling context must translate absolute heights to local indexes at
    # the V1-to-V2 multi-algorithm transition.
    transition = [
        {'block_height': height, 'version': 0x0200 + ((height % 5) << 8),
         'timestamp': 1_002_000_000 + height * 15,
         'bits': target_to_bits(POW_LIMIT)}
        for height in range(145006, 145151)
    ]
    assert next_bits(transition, {
        'block_height': 145151, 'version': 0x0200,
        'timestamp': 1_004_177_265, 'bits': 0,
    }) > 0


def test_digibyte_batch_pow_matches_scalar_pow():
    second = bytearray(80)
    second[0:4] = (0x200).to_bytes(4, 'little')
    headers = bytes(80) + bytes(second)
    batch = pow_hash_batch(headers)
    assert batch == [
        pow_hash(headers[:80], version=0, timestamp=0),
        pow_hash(headers[80:], version=0x200, timestamp=0),
    ]


def test_create_and_restore_standard_wallet():
    async def run_test():
        constants.DigiByteMainnet.set_as_network()
        wallet = None
        try:
            seed = "cycle rocket west magnet parrot shuffle foot correct salt library feed song"
            with tempfile.TemporaryDirectory() as electrum_path:
                config = SimpleConfig({'electrum_path': electrum_path, 'digibyte': True})

                keystore_from_seed = keystore.from_seed(seed, passphrase='', for_multisig=False)
                db = WalletDB('', storage=None, upgrade=True)
                db.put('keystore', keystore_from_seed.dump())
                db.put('gap_limit', 1)
                db.put('gap_limit_for_change', 1)
                wallet = Standard_Wallet(db, config=config)

                assert wallet.txin_type == 'p2pkh'
                assert wallet.get_receiving_addresses()[0] == 'DSWrS9ierLPZAqN6nyQfYgmeT5maTxfW3d'
                assert wallet.get_change_addresses()[0] == 'DPakXoJLTiFoNFn5ym1sRTiGyHD89H21mz'

                restored_keystore = keystore.from_seed(seed, passphrase='', for_multisig=False)
                assert restored_keystore.xpub == keystore_from_seed.xpub
        finally:
            if wallet is not None:
                await wallet.stop()
            constants.BitcoinMainnet.set_as_network()

    asyncio.run(run_test())

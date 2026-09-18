from electrum import constants
from electrum import bitcoin
from electrum import keystore
from electrum import util


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

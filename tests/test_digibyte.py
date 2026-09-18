from electrum import constants
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

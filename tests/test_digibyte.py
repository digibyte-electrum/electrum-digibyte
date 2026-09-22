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
from electrum.digibyte_difficulty import ODO_HEIGHT, POW_LIMIT, algorithm, next_bits, target_to_bits
from electrum.digibyte_pow import pow_hash, pow_hash_batch
from electrum.blockchain import Blockchain, deserialize_header, hash_header



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
    assert net.max_checkpoint() == net.BOOTSTRAP_CHECKPOINT_HEIGHT
    assert net.OFFICIAL_CHECKPOINT_SOURCE.endswith('src/kernel/chainparams.cpp')
    assert net.OFFICIAL_CHECKPOINTS[-1] == (
        23_500_000,
        'ade47d5ccbb92cb1d965b97a187bdbf65bf74be6a3709cb6a01339f8c2856deb')
    checkpoint = deserialize_header(bytes.fromhex(net.BOOTSTRAP_CHECKPOINT_HEADER),
                                    net.BOOTSTRAP_CHECKPOINT_HEIGHT)
    assert hash_header(checkpoint) == net.BOOTSTRAP_CHECKPOINT_HASH


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
    assert algorithm(0x0000, 145001) == 1
    assert algorithm(0x0200, 145001) == 0

    boundary = [
        {'block_height': height, 'version': 1,
         'timestamp': 1_409_580_000 + height * 60,
         'bits': 0x1c01c521}
        for height in range(144855, 145000)
    ]
    boundary[-2].update(timestamp=1409596290, bits=0x1c01f77a, version=2)
    boundary[-1].update(timestamp=1409596356, bits=0x1c01c521, version=1)
    assert next_bits(boundary, {
        'block_height': 145000, 'version': 2,
        'timestamp': 1409596362, 'bits': 0,
    }) == 0x1c01f271


def test_digibyte_batch_pow_matches_scalar_pow():
    second = bytearray(80)
    second[0:4] = (0x200).to_bytes(4, 'little')
    headers = bytes(80) + bytes(second)
    batch = pow_hash_batch(headers)
    assert batch == [
        pow_hash(headers[:80], version=0, timestamp=0),
        pow_hash(headers[80:], version=0x200, timestamp=0),
    ]


def test_digibyte_odo_activation_pow_vector():
    # Core mainnet OdoCrypt activation header at height 9,112,320.
    raw_header = bytes.fromhex(
        '020e0020ca8f5c98bc0e0c77cd4dddc76a1a6ac0b9b015a6d5e7cfd40500000000'
        '000000d6feb064acf05aaf278fd135479d0028b0aecfbac4a722c5c9fecaa260'
        'e7a673a60a355dffff001cc8acfc25'
    )
    assert len(raw_header) == 80
    assert pow_hash(raw_header, version=0x20000e02, timestamp=1563757222).hex() == (
        '8fe8946b1339262591dc2a437c29d42edb02c8c902caea06729dcd0000000000'
    )


def test_digibyte_v4_median_uses_absolute_heights_in_compressed_context():
    old = [{
        'block_height': height,
        'version': 0x20000e02,
        'timestamp': 1_563_000_000 + height,
        'bits': 0x1c00ffff,
    } for height in range(9_110_000, 9_110_010)]
    recent = [{
        'block_height': height,
        'version': 0x0200 + ((height % 5) << 8),
        'timestamp': 1_563_700_000 + height,
        'bits': 0x1c00ffff,
    } for height in range(9_114_191, 9_114_336)]

    # Sparse historical entries precede the contiguous recent window, as in
    # Blockchain's compressed runtime context.
    bits = next_bits(old + recent, {
        'block_height': 9_114_336,
        'version': 0x0200,
        'timestamp': 1_563_700_145,
        'bits': 0,
    })
    assert 0 < bits < (1 << 32)


def test_digibyte_core_v1_boundary_header_vectors():
    raw_headers = {
        144998: '02000000acd70250d387c7464b409996670b2f56d8ae13c3adf081b1278404b09c463ed9800cc86cad289753e3a544ee7316ec035b429c0212acdfc8b5e1b01ff14056dc82bb04547af7011c2984bc79',
        144999: '010000003d958255673cbc7a837764b1c82cfe9bf07ad9c70bdd41b23afe670d4eae89eac8a5e6413a4e37eac006bc71b25054306a526f31f011985c0a2608fb7d3af744c4bb045421c5011c5681d819',
        145000: '02000000288330badce1fb6c6ce47fc1834a38a0fcbb918b819ac42e1ead17d251b24ae94d461e72338b7b42115301d63b06bd6fd2f4c5d3dac1b7639e8feb796ea696c0cabb045471f2011cbe02e20a',
    }
    expected_hashes = {
        144998: 'ea89ae4e0d67fe3ab241dd0bc7d97af09bfe2cc8b16477837abc3c675582953d',
        144999: 'e94ab251d217ad1e2ec49a818b91bbfca0384a83c17fe46c6cfbe1dcba308328',
        145000: 'f8d650dda836d5e3809b928b8523f050891c3bb9fa2c201bb04824a8a2fe7df6',
    }
    headers = [deserialize_header(bytes.fromhex(raw_headers[h]), h) for h in raw_headers]
    for header in headers:
        assert hash_header(header) == expected_hashes[header['block_height']]
    assert next_bits(headers[:2], headers[2]) == 0x1c01f271


def test_digibyte_later_difficulty_era_contexts():
    version_for_algo = {0: 0x0200, 1: 0x0000, 2: 0x0400, 3: 0x0600, 4: 0x0800}
    for boundary in (400001, 1430001):
        start = boundary - 145
        headers = [
            {'block_height': height,
             'version': version_for_algo[height % 5],
             'timestamp': 1_500_000_000 + height * 15,
             'bits': target_to_bits(POW_LIMIT)}
            for height in range(start, boundary)
        ]
        bits = next_bits(headers, {
            'block_height': boundary,
            'version': version_for_algo[boundary % 5],
            'timestamp': 1_500_000_000 + boundary * 15,
            'bits': 0,
        })
        assert 0 < bits < (1 << 32)


def test_digibyte_odo_activation_uses_core_initial_target():
    headers = [{
        'block_height': height,
        'version': 0x0200 + ((height % 5) << 8),
        'timestamp': 1_562_000_000 + height * 60,
        'bits': 0x1c00ffff,
    } for height in range(ODO_HEIGHT - 145, ODO_HEIGHT)]
    candidate = {
        'block_height': ODO_HEIGHT,
        'version': 0x20000e02,
        'timestamp': 1_563_757_222,
        'bits': 0,
    }

    assert algorithm(candidate['version'], candidate['block_height']) == 7
    assert next_bits(headers, candidate) == 0x1c00ffff


def test_digibyte_v2_sparse_algorithm_history():
    headers = []
    for height in range(143136, 145174):
        # Model the sparse early-mainnet Scrypt schedule observed in Core
        # headers around the MultiAlgo transition.
        version = 1 if height % 20 == 19 else 0x0201
        headers.append({
            'block_height': height,
            'version': version,
            'timestamp': 1_409_590_000 + height * 15,
            'bits': 0x1c01c521,
        })
    bits = next_bits(headers, {
        'block_height': 145174,
        'version': 1,
        'timestamp': 1_411_005_000,
        'bits': 0,
    })
    assert bits != target_to_bits(POW_LIMIT)


def test_digibyte_context_retains_sparse_algorithm_history():
    headers = [{
        'block_height': height,
        'version': 1 if height % 30 == 0 else 0x0201,
        'timestamp': 1_409_590_000 + height * 15,
        'bits': 0x1c01c521,
    } for height in range(145001, 145601)]

    context = Blockchain._compress_digibyte_context(headers)
    scrypt_heights = [h['block_height'] for h in context if h['version'] == 1]
    assert scrypt_heights == [145320, 145350, 145380, 145410, 145440,
                              145470, 145500, 145530, 145560, 145590]


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

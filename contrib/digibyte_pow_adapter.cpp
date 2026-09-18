#include <cstdint>
#include <cstring>

#include "crypto/hashgroestl.h"
#include "crypto/hashodo.h"
#include "crypto/hashqubit.h"
#include "crypto/hashskein.h"
#include "crypto/scrypt.h"
#include "hash.h"

extern "C" int digibyte_pow_hash(const unsigned char *header, uint32_t version,
                                  uint32_t timestamp, unsigned char *output)
{
    const auto *begin = reinterpret_cast<const char *>(header);
    const auto *end = begin + 80;
    uint256 result;
    const uint32_t algo = version & (15u << 8);

    switch (algo) {
    case 0u << 8:
        scrypt_1024_1_1_256(begin, reinterpret_cast<char *>(output));
        return 0;
    case 2u << 8:
        CHash256().Write({header, 80}).Finalize(result);
        std::memcpy(output, result.data(), 32);
        return 0;
    case 4u << 8:
        result = HashGroestl(begin, end);
        break;
    case 6u << 8:
        result = HashSkein(begin, end);
        break;
    case 8u << 8:
        result = HashQubit(begin, end);
        break;
    case 14u << 8:
        result = HashOdo(begin, end, timestamp - timestamp % 60);
        break;
    default:
        return 1;
    }

    std::memcpy(output, result.data(), 32);
    return 0;
}

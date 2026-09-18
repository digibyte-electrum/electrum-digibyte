#include <cstdint>
#include <cstring>
#include <algorithm>
#include <atomic>
#include <thread>
#include <vector>

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

extern "C" int digibyte_pow_hash_batch(const unsigned char *headers, size_t count,
                                        unsigned char *outputs)
{
    if (!headers || !outputs)
        return 1;
    const unsigned int requested = std::thread::hardware_concurrency();
    const size_t workers = std::min<size_t>(count, std::min<unsigned int>(requested ? requested : 1, 8));
    std::atomic<size_t> next{0};
    std::atomic<int> error{0};
    std::vector<std::thread> pool;
    pool.reserve(workers);
    for (size_t worker = 0; worker < workers; ++worker) {
        pool.emplace_back([&]() {
            while (!error.load(std::memory_order_relaxed)) {
                const size_t index = next.fetch_add(1, std::memory_order_relaxed);
                if (index >= count)
                    return;
                const unsigned char *header = headers + index * 80;
                const uint32_t version = uint32_t(header[0]) |
                    (uint32_t(header[1]) << 8) | (uint32_t(header[2]) << 16) |
                    (uint32_t(header[3]) << 24);
                const uint32_t timestamp = uint32_t(header[68]) |
                    (uint32_t(header[69]) << 8) | (uint32_t(header[70]) << 16) |
                    (uint32_t(header[71]) << 24);
                if (digibyte_pow_hash(header, version, timestamp,
                                      outputs + index * 32)) {
                    error.store(1, std::memory_order_relaxed);
                    return;
                }
            }
        });
    }
    for (auto &worker : pool)
        worker.join();
    return error.load(std::memory_order_relaxed);
}

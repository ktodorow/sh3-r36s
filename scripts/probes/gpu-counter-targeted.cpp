/*
 * Adapted from Arm libGPUCounters api_example.cpp, pin
 * 847a04a1597d132a3746e9c6374d3977cea89a6d.
 * Copyright (c) 2023-2025 Arm Limited. SPDX-License-Identifier: MIT
 * Project changes: ten selected metrics, interval timestamps and JSON records.
 */
#include <hwcpipe/counter_database.hpp>
#include <hwcpipe/gpu.hpp>
#include <hwcpipe/sampler.hpp>

#include <array>
#include <cmath>
#include <cstdlib>
#include <ctime>
#include <iomanip>
#include <iostream>
#include <sstream>
#include <string>
#include <unistd.h>

namespace {
constexpr size_t count = 10;
const std::array<hwcpipe_counter, count> counters = {{
    MaliGPUActiveCy, MaliTilerActiveCy, MaliFragActiveCy, MaliCoreActiveCy,
    MaliEngInstr, MaliTexFiltIssueCy, MaliExtBusRdStallCy, MaliExtBusWrStallCy,
    MaliExtBusRdBy, MaliExtBusWrBy
}};
const std::array<const char *, count> names = {{
    "MaliGPUActiveCy", "MaliTilerActiveCy", "MaliFragActiveCy", "MaliCoreActiveCy",
    "MaliEngInstr", "MaliTexFiltIssueCy", "MaliExtBusRdStallCy", "MaliExtBusWrStallCy",
    "MaliExtBusRdBy", "MaliExtBusWrBy"
}};

uint64_t now(clockid_t clock) {
    timespec value{};
    if (clock_gettime(clock, &value)) {
        std::cerr << "clock_gettime failed\n";
        std::exit(255);
    }
    return uint64_t(value.tv_sec) * 1000000000ULL + uint64_t(value.tv_nsec);
}

std::string value_text(const hwcpipe::counter_sample &sample) {
    std::ostringstream out;
    if (sample.type == hwcpipe::counter_sample::type::uint64)
        out << sample.value.uint64;
    else
        out << std::setprecision(17) << sample.value.float64;
    return out.str();
}

struct frame {
    uint64_t begin{}, mono_before{}, mono_after{}, raw_before{}, raw_after{};
    std::array<std::string, count> values;
    std::string geometry;
};

bool capture(hwcpipe::sampler<> &sampler, frame &result) {
    result.mono_before = now(CLOCK_MONOTONIC);
    result.raw_before = now(CLOCK_MONOTONIC_RAW);
    auto ec = sampler.sample_now();
    result.raw_after = now(CLOCK_MONOTONIC_RAW);
    result.mono_after = now(CLOCK_MONOTONIC);
    if (ec) {
        std::cerr << "sample_now: " << ec.message() << '\n';
        return false;
    }
    hwcpipe::counter_sample sample;
    for (size_t i = 0; i < count; ++i) {
        ec = sampler.get_counter_value(counters[i], sample);
        if (ec) {
            std::cerr << names[i] << ": " << ec.message() << '\n';
            return false;
        }
        if (i == 0)
            result.begin = sample.timestamp;
        if (sample.timestamp != result.begin ||
            (sample.type == hwcpipe::counter_sample::type::float64 &&
             (!std::isfinite(sample.value.float64) || sample.value.float64 < 0))) {
            std::cerr << "Invalid timestamp or value for " << names[i] << '\n';
            return false;
        }
        result.values[i] = value_text(sample);
    }
    ec = sampler.get_counter_value(MaliGeomSampleCullRate, sample);
    if (ec) {
        std::cerr << "MaliGeomSampleCullRate: " << ec.message() << '\n';
        return false;
    }
    result.geometry = value_text(sample);
    return true;
}

void emit(const frame &sample, uint64_t end) {
    // Legacy row preserves existing capability workflow; geometry is not a limit metric.
    std::cout << "GPU Active cycles [" << sample.values[0] << "] ; Fragment Active Cycles ["
              << sample.values[2] << "] ; Geometry Sample Cull Rate [" << sample.geometry << "]\n";
    std::cout << "TARGETED_SAMPLE {\"begin_ns\":" << sample.begin << ",\"end_ns\":" << end
              << ",\"interval_ns\":" << end - sample.begin
              << ",\"request_monotonic_before_ns\":" << sample.mono_before
              << ",\"request_monotonic_after_ns\":" << sample.mono_after
              << ",\"request_raw_before_ns\":" << sample.raw_before
              << ",\"request_raw_after_ns\":" << sample.raw_after << ",\"values\":{";
    for (size_t i = 0; i < count; ++i)
        std::cout << (i ? "," : "") << '"' << names[i] << "\":" << sample.values[i];
    std::cout << "}}" << std::endl;
}
} // namespace

int main() {
    auto gpu = hwcpipe::gpu(0);
    if (!gpu) {
        std::cerr << "Mali GPU device 0 is missing\n";
        return 255;
    }
    const auto constants = gpu.get_constants();
    std::cout << " GPU Device 0:\n    Product Family: " << gpu.get_gpu_family()
              << "\n    Number of Cores: " << gpu.num_shader_cores()
              << "\n    Bus Width: " << gpu.bus_width() << '\n';
    std::cout << "TARGETED_CONSTANTS {\"gpu_id\":" << constants.gpu_id
              << ",\"shader_cores\":" << constants.num_shader_cores
              << ",\"execution_engines_per_core\":" << constants.num_exec_engines
              << ",\"l2_slices\":" << constants.num_l2_slices
              << ",\"bus_width_bits\":" << constants.axi_bus_width
              << ",\"monotonic_ns\":" << now(CLOCK_MONOTONIC)
              << ",\"raw_ns\":" << now(CLOCK_MONOTONIC_RAW) << "}\n";
    auto database = hwcpipe::counter_database{};
    hwcpipe::counter_metadata metadata;
    std::cout << " GPU 0 Supported counters:\n";
    for (auto counter : database.counters_for_gpu(gpu)) {
        auto ec = database.describe_counter(counter, metadata);
        if (ec) {
            std::cerr << "describe_counter: " << ec.message() << '\n';
            return 255;
        }
        std::cout << "    " << metadata.name << '\n';
    }
    std::cout << " Sample Capture:\n";
    auto config = hwcpipe::sampler_config(gpu);
    for (auto counter : counters) {
        auto ec = config.add_counter(counter);
        if (ec) {
            std::cerr << "Counter " << counter << " unsupported: " << ec.message() << '\n';
            return 255;
        }
    }
    auto ec = config.add_counter(MaliGeomSampleCullRate);
    if (ec) {
        std::cerr << "Legacy geometry counter unsupported: " << ec.message() << '\n';
        return 255;
    }
    auto sampler = hwcpipe::sampler<>(config);
    ec = sampler.start_sampling();
    if (ec) {
        std::cerr << "start_sampling: " << ec.message() << '\n';
        return 255;
    }
    frame previous;
    if (!capture(sampler, previous)) // Discard library-start / first-driver boundary mix.
        return 255;
    for (unsigned i = 0; i <= 10; ++i) {
        if (i < 10)
            usleep(100000);
        frame current;
        if (!capture(sampler, current))
            return 255;
        if (i > 0) {
            // API timestamp is interval BEGIN. Next begin is previous driver end.
            if (current.begin <= previous.begin) {
                std::cerr << "Non-increasing driver timestamps\n";
                return 255;
            }
            emit(previous, current.begin);
        }
        previous = current;
    }
    ec = sampler.stop_sampling();
    if (ec) {
        std::cerr << "stop_sampling: " << ec.message() << '\n';
        return 255;
    }
    return 0;
}

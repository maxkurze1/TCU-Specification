#!/bin/sh

cargo build --release && \
    cp target/x86_64-unknown-linux-gnu/release/libnocrw.so ../python/nocrw.so


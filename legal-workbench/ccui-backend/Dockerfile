FROM rust:1.84-bookworm AS builder
WORKDIR /build
COPY Cargo.toml Cargo.lock ./
COPY src/ src/
RUN cargo build --release

FROM debian:bookworm-slim
RUN apt-get update && apt-get install -y --no-install-recommends tmux ca-certificates && rm -rf /var/lib/apt/lists/*
COPY --from=builder /build/target/release/ccui-backend /usr/local/bin/
ENV RUST_LOG=info
EXPOSE 8005
CMD ["ccui-backend"]

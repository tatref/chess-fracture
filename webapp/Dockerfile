FROM ekidd/rust-musl-builder AS builder

#WORKDIR /work
COPY . .
RUN sudo chown -R rust:rust .

#VOLUME /home/rust/.cargo

RUN cargo build --release



FROM alpine

WORKDIR /work
COPY --from=builder /home/rust/src/target/x86_64-unknown-linux-musl/release/webapp .
#COPY --from=builder /work/target/release/webapp .

CMD ./webapp

import strawberry


@strawberry.scalar(
    name="BigInt",
    description="Arbitrary size integer for values larger than 32-bit GraphQL Int",
)
def BigInt(value: int) -> int:
    # Strawberry just needs something that can serialize/parse.
    # Python's int is already arbitrary-precision, so we just cast.
    return int(value)

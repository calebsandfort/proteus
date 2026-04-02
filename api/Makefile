.PHONY: test test-verbose test-cov build run restore

# Run tests with xUnit
test:
	dotnet test

# Run tests with verbose output
test-verbose:
	dotnet test --logger "console;verbosity=detailed"

# Run tests with coverage
test-cov:
	dotnet test --collect:"XPlat Code Coverage"

# Build the project
build:
	dotnet build

# Run the API
run:
	dotnet run

# Restore dependencies
restore:
	dotnet restore

# Run a specific test class
test-class:
	dotnet test --filter "ClassName=$(CLASS)"

# Run tests matching a pattern
test-match:
	dotnet test --filter "FullyQualifiedName~$(PATTERN)"

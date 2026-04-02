.PHONY: test test-verbose test-cov build run restore

# Run tests with xUnit
test:
	dotnet test

# Run tests with verbose output
test-verbose:
	dotnet test --logger "console;verbosity=detailed"

# Run tests with coverage using dotnet-coverage (required for .NET 10+)
test-cov:
	rm -rf TestResults && dotnet-coverage collect 'dotnet test' -o './TestResults/coverage.cobertura.xml' -f cobertura

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

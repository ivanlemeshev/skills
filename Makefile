.DEFAULT_GOAL := check
VERSION ?= $(shell cat VERSION)

.PHONY: check release

check:
	python3 -B -m unittest discover -s skills/lem-factory/tests -v
	gh skill publish --dry-run

release: check
	@test "$$(git branch --show-current)" = main || { echo 'Run the release from main.'; exit 1; }
	@test -n '$(VERSION)' || { echo 'Set VERSION before the release.'; exit 1; }
	printf '%s\n' '$(VERSION)' > VERSION
	git add --all
	git diff --cached --check
	@if ! git diff --cached --quiet; then git commit -m 'Release v$(VERSION)'; fi
	git push origin main
	gh skill publish --tag 'v$(VERSION)'

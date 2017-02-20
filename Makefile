ci: test lint
	@echo "CI complete"

lint:
	@echo "Running pylint"
	@pylint python_template tests pylint_custom --msg-template="{path}:{line}:{column} {msg_id}({symbol}) {msg}"

test:
	@echo "Running pytest"
	@py.test tests

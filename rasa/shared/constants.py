DOCS_BASE_URL = "https://rasa.com/docs/rasa"
LEGACY_DOCS_BASE_URL = "https://legacy-docs-v1.rasa.com"
DOCS_URL_TRAINING_DATA_NLU = DOCS_BASE_URL + "/nlu/training-data-format/"
DOCS_URL_DOMAINS = DOCS_BASE_URL + "/core/domains/"
DOCS_URL_STORIES = DOCS_BASE_URL + "/core/stories/"
DOCS_URL_RULES = DOCS_BASE_URL + "/core/rules/"
DOCS_URL_FORMS = DOCS_BASE_URL + "/core/forms/"
DOCS_URL_POLICIES = DOCS_BASE_URL + "/core/policies/"
DOCS_URL_TEST_STORIES = DOCS_BASE_URL + "/testing-your-assistant"
DOCS_URL_ACTIONS = DOCS_BASE_URL + "/core/actions/"
DOCS_URL_CONNECTORS = DOCS_BASE_URL + "/user-guide/connectors/"
DOCS_URL_EVENT_BROKERS = DOCS_BASE_URL + "/api/event-brokers/"
DOCS_URL_PIKA_EVENT_BROKER = DOCS_URL_EVENT_BROKERS + "#pika-event-broker"
DOCS_URL_TRACKER_STORES = DOCS_BASE_URL + "/api/tracker-stores/"
DOCS_URL_PIPELINE = DOCS_BASE_URL + "/nlu/choosing-a-pipeline/"
DOCS_URL_COMPONENTS = DOCS_BASE_URL + "/nlu/components/"
DOCS_URL_MIGRATION_GUIDE = DOCS_BASE_URL + "/migration-guide/"
DOCS_BASE_URL_RASA_X = "https://rasa.com/docs/rasa-x"

INTENT_MESSAGE_PREFIX = "/"

PACKAGE_NAME = "rasa"

CONFIG_SCHEMA_FILE = "shared/nlu/training_data/schemas/config.yml"
RESPONSES_SCHEMA_FILE = "shared/nlu/training_data/schemas/responses.yml"
SCHEMA_EXTENSIONS_FILE = "shared/utils/pykwalify_extensions.py"
LATEST_TRAINING_DATA_FORMAT_VERSION = "2.0"

DOMAIN_SCHEMA_FILE = "utils/schemas/domain.yml"

DEFAULT_SESSION_EXPIRATION_TIME_IN_MINUTES = 0
DEFAULT_CARRY_OVER_SLOTS_TO_NEW_SESSION = True

DEFAULT_NLU_FALLBACK_INTENT_NAME = "nlu_fallback"

DEFAULT_E2E_TESTS_PATH = "tests"
TEST_STORIES_FILE_PREFIX = "test_"

DEFAULT_LOG_LEVEL = "INFO"
ENV_LOG_LEVEL = "LOG_LEVEL"

DEFAULT_SENDER_ID = "default"

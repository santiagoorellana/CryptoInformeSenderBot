
from core import Core
from basics import log
from report import *


def analyze_market(config:Dict):
    for currencyBase in config["currencies"]:
        config["currencyBase"] = currencyBase
        core = Core(config)
        if core.exchange.check_exchange_methods(False):
            if core.exchange.load_markets_and_currencies():
                marketData = core.get_data_of_market()
                if marketData is not None:
                    core.analyze_market(marketData)
                    log.info('\nTERMINADO OK')
                    return True
        log.info('\nTERMINADO: No se puede continuar.')
        return False


 
from fastapi import FastAPI
from operator import itemgetter
import uvicorn
import json

CO2_PRODUCTION = 0.3

app = FastAPI()

class PowerDistribution:

    _distribution = []

    def __init__(self, specs):
        self._distribution = []
        self.objectiveCopy = specs["load"]
        self.objective = specs["load"]
        self.gasPrice = specs["fuels"]["gas(euro/MWh)"]
        self.kerosinePrice = specs["fuels"]["kerosine(euro/MWh)"]
        self.co2price = specs["fuels"]["co2(euro/ton)"]
        self.windSpeed = specs["fuels"]["wind(%)"]
        self.powerplants = specs["powerplants"]

    def resetData(self):
        self._distribution.clear()
        self.objective = self.objectiveCopy

    def getDistribution(self):
        return self._distribution

    def sort_by_cost_efficiency_with_co2(self):
        for plant in self.powerplants:
            if plant["type"] == "gasfired":
                plant["cost_per_elec_unit"] = self.gasPrice / plant["efficiency"] + CO2_PRODUCTION * self.co2price
            elif plant["type"] == "turbojet":
                plant["cost_per_elec_unit"] = self.kerosinePrice / plant["efficiency"]
            else:
                plant["cost_per_elec_unit"] = 0
        self.powerplants = sorted(self.powerplants, key=itemgetter("cost_per_elec_unit"))

    def sort_by_cost_efficiency(self):
        for plant in self.powerplants:
            if plant["type"] == "gasfired":
                plant["cost_per_elec_unit"] = self.gasPrice / plant["efficiency"]
            elif plant["type"] == "turbojet":
                plant["cost_per_elec_unit"] = self.kerosinePrice / plant["efficiency"]
            else:
                plant["cost_per_elec_unit"] = 0
        self.powerplants = sorted(self.powerplants, key=itemgetter("cost_per_elec_unit"))

    def compute_windturbines(self):
        for plant in self.powerplants:
            if plant["type"] == "windturbine":
                if self.objective > plant["pmax"] * self.windSpeed / 100:
                    power = plant["pmax"] * self.windSpeed / 100
                    self._distribution.append(dict(name=plant["name"], p=power))
                    self.objective -= self._distribution[-1]["p"]
                else:
                    power = self.objective
                    self._distribution.append(dict(name=plant["name"], p=power))
                    self.objective -= self._distribution[-1]["p"]
                    return

    def compute_paying_energy(self):
        for idx, plant in enumerate(self.powerplants):
            if self.objective == 0:
                self._distribution.append(dict(name=plant["name"], p=0))
                continue
            if plant["type"] == "windturbine":
                continue
            elif plant["type"] == "gasfired":
                if self.objective > plant["pmin"]:
                    if self.objective > plant["pmax"]:
                        power = plant["pmax"]
                        self._distribution.append(dict(name=plant["name"], p=power))
                        self.objective -= self._distribution[-1]["p"]
                    else:
                        power = self.objective
                        self._distribution.append(dict(name=plant["name"], p=power))
                        self.objective -= self._distribution[-1]["p"]
                        return
                else:
                    for i in range (idx - 1, 0, -1):
                        if self.powerplants[i]["pmax"] - plant["pmin"] > self.powerplants[i]["pmin"]:
                            power = plant["pmin"] + self.objective
                            self._distribution[i]["p"] -= plant["pmin"]
                            self._distribution.append(dict(name=plant["name"], p=power))
                            self.objective -= self._distribution[-1]["p"]
                            return
            else:
                if self.objective > plant["pmax"]:
                    power = plant["pmax"]
                    self._distribution.append(dict(name=plant["name"], p=power))
                    self.objective -= self._distribution[-1]["p"]
                else:
                    power = self.objective
                    self._distribution.append(dict(name=plant["name"], p=power))
                    self.objective -= self._distribution[-1]["p"]
                    return



@app.get("/")
def read_root():
    name = "PowerPlant Coding Challenge"
    author = "Carl-Olivier N'Diaye"
    version = "1.0.0"
    return dict(name=name, author=author, version=version)


@app.post("/powerplant")
def powerplant(payload: str):
    payload_dict = json.loads(payload)
    P = PowerDistribution(payload_dict)
    P.compute_windturbines()
    P.sort_by_cost_efficiency()
    P.compute_paying_energy()
    distribution = P.getDistribution()
    return distribution

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8888)
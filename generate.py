#!/usr/bin/env python3

import argparse, contextlib, functools, io, json, logging, os, re, requests, shutil, subprocess, tempfile, zipfile

MODPACK_NAME = "Mekka"
MINECRAFT_VERSION = "1.21.1"
NEOFORGE_VERSION = "21.1.218"
MODPACK_VERSION = "0.1.0"

NEOFORGE_URL = f"https://maven.neoforged.net/releases/net/neoforged/neoforge/{NEOFORGE_VERSION}/neoforge-{NEOFORGE_VERSION}-installer.jar"

MOD_IDS = {
    "Xaero's Minimap" : "puXrtfcK",
    "Xaero's World Map" : "xUpTkg0V",
    "AppleSkin" : "kztxpjAA",
    "TerraBlender" : "6e8GCrLb",
    "Biomes O' Plenty" : "8vIRXPpR",
    "GlitchCore" : "8wmCpbQ2",
    "Jade" : "VGRMP69T",
    "Jade Addons" : "Z9s9lM56",
    "EMI" : "ouSj7NfF",
    "Artifacts" : "bYbUZqGA",
    "Lithium" : "G5SDYehn",
    "Tree Harvester" : "OtzwmSlR",
    "Collective" : "VTg6femX",
    "Veinminer" : "jEnnLun7",
    "Distant Horizons" : "bLPLghy9",
    "Mekanism" : "D32JUF51",
    "Mekanism Generators" : "bPzSK3o5",
    "Mekanism Tools" : "KiWtMI2k",
    "Mekanism Additions" : "wfPjzfo0",
    "Farmer's Delight" : "opCbq7uB",
    "Storage Drawers" : "px0CCB06",
    "GraveStone Mod" : "AZm51eX1",
    "RightClickHarvest" : "fVhkJu1j",
    "Sophisticated Backpacks" : "ovVp31Ci",
    "FerriteCore" : "CnpoQxCx",
    "YUNG's API" : "ZB22DE9q",
    "YUNG's Better Nether Fortresses" : "iopJiJQp",
    "YUNG's Better Ocean Monuments" : "yFjEcj2g",
    "YUNG's Better Dungeons" : "D6aZn0Em",
    "YUNG's Better Mineshafts" : "Go3nbneL",
    "YUNG's Better Jungle Temples" : "P00i2hJn",
    "YUNG's Better End Island" : "I52NZ1qK",
    "YUNG's Better Strongholds" : "8U0dIfSM",
    "YUNG's Better Desert Temples" : "GQ9iNWkI",
    "YUNG's Bridges" : "urkCzBf6",
    "YUNG's Extras" : "N2EpMhR7",
    "Architectury API" : "ZxYGwlk0",
    "Cloth Config API" : "izKINKFg",
    "JamLib" : "8Ph8BKRh",
    "Sophisticated Core" : "BteMlDq5",
    "ModernFix" : "8Be8uJW6",
    "Clumps" : "jo7lDoK4",
    "Applied Energistics 2" : "kfyIqgJ6",
    "GuideMe" : "ILW6vM7o",
    "Sinytra Connector" : "YCMXHxwl",
    "Forgified Fabric API" : "tIUhtT2C",
    "Accessories" : "CtRim6mz",
    "owo" : "NMCHU6DZ",
    "ChoiceTheorem's Overhauled Village" : "z24vsFwz",
    "Lithostitched" : "HsoCbRc0",
    "Nature's Copmpass" : "AqEmYPpi",
    "Explorer's Compass" : "EpWAw9bz",
    "ME Requester" : "kkJqmO8M",
    "Waystones" : "f4A1aY3t",
    "Balm" : "Yoii3Xj6",
}

MOD_IDS_SERVER = {
    "Chunky" : "LuFhm4eU",
} | MOD_IDS

MOD_IDS_CLIENT = {
    "Sodium" : "Pb3OXVqC",
    "Iris" : "t3ruzodq",
    "Entity Culling" : "DwB2BGbW",
    "Better Advancements" : "FjTYILOi",
    "BetterF3" : "maXNB1dn",
    "ImmediatelyFast" : "7TFPpGUU",
    "Continuity" : "eXGUs5sy",
    "Mouse Tweaks" : "9I21YYxf",
} | MOD_IDS

RESOURCE_PACKS = {
    "Fast Better Grass" : "xteFNcow"
}

SHADERS = {
    "BSL Shaders" : "3WGx0wKu",
    "Complementary Shaders - Unbound" : "LXrX6oqm",
    "Complementary Shaders - Reimagined" : "OfRF7dTR",
}

MODPACK_FILENAME = f"{MODPACK_NAME.lower().replace(' ', '_')}_MC{MINECRAFT_VERSION}_v{MODPACK_VERSION}_client.mrpack"

MODRINTH_INDEX = {
    "formatVersion": 1,
    "game": "minecraft",
    "versionId": MODPACK_VERSION,
    "name": MODPACK_NAME,
    "dependencies": {
        "minecraft": MINECRAFT_VERSION,
        "neoforge": NEOFORGE_VERSION
    },
    "files": []
}

CLIENT_OPTIONS = [
    f"fullscreen:true",
    f"guiScale:2",
    f"renderDistance:8",
    f"simulationDistance:8",
    f"resourcePacks:[\"vanilla\",\"fabric\",\"bountifulfares:vanilla_item_override\",\"file/Fast Better Grass.zip\"]",
]

SERVER_PROPERTIES = [
    f"motd=Welcome to the {MODPACK_NAME} Neoforge Server!",
    f"view-distance=8",
    f"simulation-distance=8",
    f"gamemode=survival",
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(message)s")

MODDED_ORES = [
    "mekanism:lead_ore",
    "mekanism:deepslate_lead_ore",
    "mekanism:fluorite_ore",
    "mekanism:deepslate_fluorite_ore",
    "mekanism:uranium_ore",
    "mekanism:deepslate_uranium_ore",
    "mekanism:osmium_ore",
    "mekanism:deepslate_osmium_ore",
    "mekanism:tin_ore",
    "mekanism:deepslate_tin_ore",
]

# LOGGING DECORATORS ===================================================================================================================================================================================

def archiveFolderLog(f):
    w = lambda p, a: [logging.info(f"Archiving the \"{p}\" folder to \"{a}\" archive"), f(p, a)][1]; return w

def downloadFileLog(f):
    w = lambda u, d: [logging.info(f"Downloading the \"{u}\" file to \"{d}\""), f(u, d)][1]; return w

def executeCommandLog(f):
    w = lambda c: [logging.info(f"Executing the \"{c}\" command"), f(c)][1]; return w

def getModMetadataLog(f):
    w = lambda n, i: [logging.info(f"Fetching metadata for the \"{n}\" with ID \"{i}\""), f(n, i)][1]; return w

# DEFINED FUNCTIONS ====================================================================================================================================================================================

@archiveFolderLog
def archiveFolder(folder_path, archive_name):
    shutil.make_archive(archive_name, "zip", folder_path); shutil.move(f"{archive_name}.zip", archive_name)

@downloadFileLog
def downloadFile(url, dest):
    with open(dest, "wb") as file: file.write(requests.get(url).content)

def downloadMod(mod_metadata, dest_dir):
    os.path.exists(path := os.path.join(dest_dir, mod_metadata["files"][0]["filename"])) or downloadFile(mod_metadata["files"][0]["url"], path)

@executeCommandLog
def executeCommand(command):
    subprocess.run(command, capture_output=False, shell=True, stdout=subprocess.DEVNULL)

def filterLines(string, prefix):
    return "\n".join([line for line in string.split("\n") if not line.startswith(prefix)])

@getModMetadataLog
def getModMetadata(name, mod_id):
    return requests.get(f"https://api.modrinth.com/v2/version/{mod_id}").json()

def generateModEntry(mod_metadata):
    return {
        "path": f"mods/{mod_metadata['files'][0]['filename']}",
        "hashes": {
            "sha1": mod_metadata["files"][0]["hashes"]["sha1"],
            "sha512": mod_metadata["files"][0]["hashes"]["sha512"]
        },
        "env": {
            "client": "required",
            "server": "required"
        },
        "downloads": [
            mod_metadata["files"][0]["url"]
        ],
        "fileSize": mod_metadata["files"][0]["size"]
    }

def modifyZip(path, function):
    temp = tempfile.TemporaryDirectory(); zipfile.ZipFile(path).extractall(temp.name); function(temp.name); archiveFolder(temp.name, path); temp.cleanup()

def readFile(filename):
    with open(filename, "r") as file: return file.read()

def replaceInFile(filename, old, new):
    writeToFile(filename, readFile(filename).replace(old, new))

def writeToFile(filename, content):
    with open(filename, "w") as file: file.write(content + "\n")

# SHADER FIXING FUNCTION ===============================================================================================================================================================================

def fixComplementaryUnbound(directory):
    replaceInFile(os.path.join(directory, "shaders", "block.properties"), "block.10024=", f"block.10024={' '.join(MODDED_ORES)}")

# MAIN EXECUTION =======================================================================================================================================================================================

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog=os.path.basename(__file__), description="Server and Client Generator for the {MODPACK_NAME} Modpack",
        formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=128),
        add_help=False, allow_abbrev=False
    )

    parser.add_argument("-h", "--help", action="help", default=argparse.SUPPRESS, help="This help message.")

    parser.add_argument("--client", action="store_true", help="Generate the client modpack.")
    parser.add_argument("--server", action="store_true", help="Generate the server files.")

    parser.add_argument("--memory", type=str, default="4G", help="Maximum memory allocation for the server.")

    args = parser.parse_args()

    def modpack(directory):
        os.makedirs(os.path.join(directory, "overrides", "resourcepacks"), exist_ok=True)
        os.makedirs(os.path.join(directory, "overrides", "shaderpacks"  ), exist_ok=True)

        for mod in MOD_IDS_CLIENT.items():
            MODRINTH_INDEX["files"].append(generateModEntry(getModMetadata(*mod)))

        for resource in RESOURCE_PACKS.items():
            downloadMod(getModMetadata(*resource), os.path.join(directory, "overrides", "resourcepacks"))

        for shader in SHADERS.items():

            metadata = getModMetadata(*shader)

            downloadMod(metadata, os.path.join(directory, "overrides", "shaderpacks"))

            if shader[0] == "Complementary Shaders - Unbound": modifyZip(os.path.join(directory, "overrides", "shaderpacks", metadata["files"][0]["filename"]), fixComplementaryUnbound)

        writeToFile(os.path.join(directory, "modrinth.index.json"     ), json.dumps(MODRINTH_INDEX, indent=4))
        writeToFile(os.path.join(directory, "overrides", "options.txt"), "\n".join(CLIENT_OPTIONS)           )

        shutil.copytree("config", os.path.join(directory, "overrides", "config"), dirs_exist_ok=True)

        archiveFolder(directory, MODPACK_FILENAME)

    def mserver(directory):
        os.makedirs("server", exist_ok=True)

        downloadFile(NEOFORGE_URL, os.path.join("server", "server.jar"))

        writeToFile(os.path.join("server", "run.sh" ), f"java -jar server.jar")

        os.chmod(os.path.join("server", "run.sh"), 0o755)

        writeToFile(os.path.join("server", "eula.txt"         ), f"eula=true"                )
        writeToFile(os.path.join("server", "server.properties"), "\n".join(SERVER_PROPERTIES))

        os.makedirs(os.path.join("server", "mods"), exist_ok=True)

        for mod in (item for item in MOD_IDS_SERVER.items() if args.server):
            downloadMod(getModMetadata(*mod), os.path.join("server", "mods"))

        shutil.copytree("config", os.path.join("server", "config"), dirs_exist_ok=True)

    with tempfile.TemporaryDirectory() as temp: modpack(temp) if args.client else None
    with tempfile.TemporaryDirectory() as temp: mserver(temp) if args.server else None

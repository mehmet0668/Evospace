#!/usr/bin/env python3
import argparse
import json
import os
from pathlib import Path
import subprocess
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser(description="EvoSpace görsel simülasyon (Qt-OpenGL) başlatıcı")
    parser.add_argument("--task", choices=["apc", "nc", "cc"], default="apc", help="Görev: apc, nc veya cc")
    parser.add_argument("--genome", type=int, default=1, help="Genom numarası (1-10 arası, varsayılan: 1)")
    parser.add_argument("--seed", type=int, default=2001, help="Rastgele tohum (seed)")
    args = parser.parse_args()

    r = json.loads((ROOT / "runtime/base/runtime.json").read_text(encoding="utf-8"))
    e = json.loads((ROOT / "runtime/evospace/runtime.json").read_text(encoding="utf-8"))

    qtopengl_sos = list((ROOT / "runtime/gui/build").rglob("*qtopengl*.so"))
    if not qtopengl_sos:
        raise FileNotFoundError("qtopengl .so dosyası bulunamadı!")
    gui_plugin_dir = str(qtopengl_sos[0].parent)

    original_xml = ROOT / f"02_EvoSpace/source/experiments/mate/neat_{args.task}_visu.xml"
    tree = ET.parse(original_xml)
    root = tree.getroot()

    genome_path = ROOT / f"02_EvoSpace/genomes/{args.task}/gen_{args.genome - 1}"

    controller = root.find("controllers")[0]
    old_id = controller.get("id")
    controller.tag = "nn_rm_3Dot1_controller"
    controller.set("id", "nn_rm_3Dot1_controller")
    controller.set("library", e["library"])
    params = controller.find("params")
    if params is not None:
        params.set("genome_file", str(genome_path))

    for element in root.findall(".//arena//controller"):
        if element.get("config") == old_id:
            element.set("config", "nn_rm_3Dot1_controller")

    # Tüm arenayı yukarıdan net görmek için kamerayı kuş bakışı ayarla
    cam = root.find(".//visualization/qt-opengl/camera/placements/placement[@index='0']")
    if cam is not None:
        cam.set("position", "0,0,4.5")
        cam.set("look_at", "0,0,0")
        cam.set("up", "0,1,0")

    root.find("framework/experiment").set("random_seed", str(args.seed))
    root.find("loop_functions").set("library", r["metrics"][args.task])

    demo_dir = ROOT / "runs/demo_visu"
    demo_dir.mkdir(parents=True, exist_ok=True)
    config_path = demo_dir / f"visu_{args.task}_g{args.genome}.xml"
    tree.write(config_path, encoding="utf-8", xml_declaration=True)

    command = [e["binary"], "-c", str(config_path), "-g", str(genome_path), "-s", str(args.seed)]

    env = os.environ.copy()
    gui_epuck_dir = str(ROOT / "runtime/gui/build/plugins/robots/e-puck")
    env["ARGOS_PLUGIN_PATH"] = f"{gui_plugin_dir}:{gui_epuck_dir}:{r['plugin_dir']}"
    env["LD_LIBRARY_PATH"] = ":".join([
        e["build_dir"],
        gui_plugin_dir,
        r["plugin_dir"],
        str(Path(r["prefix"]) / "lib"),
    ])

    print(f"Başlatılıyor: Görev={args.task.upper()}, Genom={args.genome}, Seed={args.seed}")
    subprocess.run(command, cwd=demo_dir, env=env)

if __name__ == "__main__":
    main()

import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.db.session import SessionLocal, engine
from app.db.models import User
from app.core.security import get_password_hash
from sqlalchemy import text

MAPPERS = [
    {
        "nama": "Anggita Maharani",
        "nim": "22/494471/SV/20837",
        "username": "anggita_maharani",
        "email": "anggita.maharani@mail.ugm.ac.id",
    },
    {
        "nama": "Devinta Cahaya Putri",
        "nim": "22/506129/SV/22075",
        "username": "devinta_cahaya_putri",
        "email": "devinta.cahaya.putri@mail.ugm.ac.id",
    },
    {
        "nama": "Dhiva Nur Isnaeni",
        "nim": "22/506069/SV/22054",
        "username": "dhiva_nur_isnaeni",
        "email": "dhiva.nur.isnaeni@mail.ugm.ac.id",
    },
    {
        "nama": "Farmana Ditya Alya Safitri",
        "nim": "22/493937/SV/20758",
        "username": "farmana_ditya_alya_safitri",
        "email": "farmana.ditya.alya.safitri@mail.ugm.ac.id",
    },
    {
        "nama": "Hanantarini Sanastri",
        "nim": "22/499664/SV/21354",
        "username": "hanantarini_sanastri",
        "email": "hanantarini.sanastri@mail.ugm.ac.id",
    },
    {
        "nama": "Khairunnisa Dewi Ratih",
        "nim": "22/494397/SV/20800",
        "username": "khairunnisa_dewi_ratih",
        "email": "khairunnisa.dewi.ratih@mail.ugm.ac.id",
    },
    {
        "nama": "Mardhiyah Auliya Rahman Lubis",
        "nim": "23/513607/SV/22236",
        "username": "mardhiyah_auliya_rahman_lubis",
        "email": "mardhiyah.auliya.rahman.lubis@mail.ugm.ac.id",
    },
    {
        "nama": "Meyna Anjar Nilawati",
        "nim": "22/494861/SV/20925",
        "username": "meyna_anjar_nilawati",
        "email": "meyna.anjar.nilawati@mail.ugm.ac.id",
    },
    {
        "nama": "Miftah Desma Syahputra",
        "nim": "22/505796/SV/21938",
        "username": "miftah_desma_syahputra",
        "email": "miftah.desma.syahputra@mail.ugm.ac.id",
    },
    {
        "nama": "Muhammad Fauzil Adhim Sulistyo",
        "nim": "23/521853/SV/23514",
        "username": "muhammad_fauzil_adhim_sulistyo",
        "email": "muhammad.fauzil.adhim.sulistyo@mail.ugm.ac.id",
    },
    {
        "nama": "Nurul Halimah",
        "nim": "22/502928/SV/21457",
        "username": "nurul_halimah",
        "email": "nurul.halimah@mail.ugm.ac.id",
    },
    {
        "nama": "Putri Shafaa Salsabila",
        "nim": "22/496510/SV/20967",
        "username": "putri_shafaa_salsabila",
        "email": "putri.shafaa.salsabila@mail.ugm.ac.id",
    },
    {
        "nama": "Rasyidini Ayu Rahmawati",
        "nim": "22/499856/SV/21374",
        "username": "rasyidini_ayu_rahmawati",
        "email": "rasyidini.ayu.rahmawati@mail.ugm.ac.id",
    },
    {
        "nama": "Risma Enggar Sri Kawurihan",
        "nim": "22/505658/SV/21862",
        "username": "risma_enggar_sri_kawurihan",
        "email": "risma.enggar.sri.kawurihan@mail.ugm.ac.id",
    },
    {
        "nama": "Setia Rizki Wibowo",
        "nim": "22/506031/SV/22041",
        "username": "setia_rizki_wibowo",
        "email": "setia.rizki.wibowo@mail.ugm.ac.id",
    },
    {
        "nama": "Tita Amalia Sudarma",
        "nim": "22/492643/SV/20594",
        "username": "tita_amalia_sudarma",
        "email": "tita.amalia.sudarma@mail.ugm.ac.id",
    },
    {
        "nama": "Trisna Diah Ayu Wulandari",
        "nim": "22/505883/SV/21979",
        "username": "trisna_diah_ayu_wulandari",
        "email": "trisna.diah.ayu.wulandari@mail.ugm.ac.id",
    },
    {
        "nama": "Virnanda Nur Mahanani",
        "nim": "22/499290/SV/21298",
        "username": "virnanda_nur_mahanani",
        "email": "virnanda.nur.mahanani@mail.ugm.ac.id",
    },
    {
        "nama": "Wahyu Eka Saputra",
        "nim": "22/492888/SV/20629",
        "username": "wahyu_eka_saputra",
        "email": "wahyu.eka.saputra@mail.ugm.ac.id",
    },
    {
        "nama": "Zahra Pramudita",
        "nim": "22/492630/SV/20591",
        "username": "zahra_pramudita",
        "email": "zahra.pramudita@mail.ugm.ac.id",
    },
]

DEFAULT_PASSWORD = "mapper123"

def seed_mappers(db: Session):
    hashed_pwd = get_password_hash(DEFAULT_PASSWORD)
    created_count = 0
    updated_count = 0

    for idx, m in enumerate(MAPPERS, 1):
        user = db.query(User).filter(
            (User.username == m["username"]) |
            (User.email == m["email"]) |
            (User.nim_nip == m["nim"]) |
            (User.full_name == m["nama"])
        ).first()

        if user:
            user.username = m["username"]
            user.full_name = m["nama"]
            user.nim_nip = m["nim"]
            user.institution = user.institution or "Sekolah Vokasi - UGM"
            user.department = user.department or "DTK"
            user.role = "annotator"
            user.is_active = True
            updated_count += 1
        else:
            user = User(
                username=m["username"],
                email=m["email"],
                full_name=m["nama"],
                hashed_password=hashed_pwd,
                role="annotator",
                is_active=True,
                nim_nip=m["nim"],
                institution="Sekolah Vokasi - UGM",
                department="DTK"
            )
            db.add(user)
            created_count += 1

    db.commit()

    if engine.dialect.name == "postgresql":
        try:
            db.execute(text("SELECT setval('users_id_seq', COALESCE((SELECT MAX(id) FROM users), 1), true);"))
            db.commit()
        except Exception as e:
            pass

    return created_count, updated_count

def main():
    db = SessionLocal()
    try:
        created, updated = seed_mappers(db)
        print(f"Done! Created: {created}, Updated: {updated}. Default password: {DEFAULT_PASSWORD}")
    finally:
        db.close()

if __name__ == "__main__":
    main()

# ============================================================
# models.py
# File ini mendefinisikan "bentuk" tabel di database kita.
# Satu class = satu tabel. Ini yang disebut ORM (Object Relational Mapper):
# kita tulis class Python, SQLAlchemy yang urus SQL-nya.
# ============================================================

from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from database import Base

# Class User merepresentasikan tabel bernama "users" di database.
# Setiap atribut (id, username, dll) = satu kolom di tabel.
class User(Base):

    # __tablename__ menentukan nama tabel di database
    __tablename__ = "users"

    # Column(Integer, primary_key=True) → kolom angka, ID unik tiap user
    # index=True supaya pencarian berdasarkan ID lebih cepat
    id = Column(Integer, primary_key=True, index=True)

    # Column(String) → kolom teks
    # unique=True → tidak boleh ada username yang sama
    # index=True → pencarian username lebih cepat
    username = Column(String, unique=True, index=True, nullable=False)

    # Email juga harus unik, tidak boleh ada yang sama
    email = Column(String, unique=True, index=True, nullable=False)

    # Password disimpan plain text (teks biasa) untuk tujuan pembelajaran.
    # CATATAN PENTING: Di aplikasi nyata, password HARUS di-hash!
    # Materi hashing akan dibahas di modul Kriptografi nanti.
    password = Column(String, nullable=False)

    # Nama lengkap user, boleh kosong (nullable=True adalah default)
    full_name = Column(String, nullable=True)

    # Nama file foto profil. Kosong kalau belum upload.
    photo = Column(String, nullable=True)

    # Relasi ke tabel tasks
    tasks = relationship("Task", back_populates="owner", cascade="all, delete-orphan")

class Task(Base):

    # __tablename__ menentukan nama tabel di database
    __tablename__ = "tasks"

    # Kolom utama tugas
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    status = Column(String, nullable=False, default="pending")
    is_completed = Column(Boolean, nullable=False, default=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    attachment_file = Column(String, nullable=True)
    attachment_name = Column(String, nullable=True)

    # Hubungkan tugas ke pengguna pemiliknya
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="tasks")
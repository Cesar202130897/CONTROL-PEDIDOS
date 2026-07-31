import streamlit as st
import sqlite3
from datetime import datetime

st.set_page_config(page_title="Control de Pedidos", layout="centered", page_icon="🥩")

# Conexión a la base de datos
conn = sqlite3.connect('carniceria.db', check_same_thread=False)
c = conn.cursor()

c.execute('''CREATE TABLE IF NOT EXISTS clientes (id INTEGER PRIMARY KEY, nombre TEXT)''')
c.execute('''CREATE TABLE IF NOT EXISTS pedidos 
             (id INTEGER PRIMARY KEY AUTOINCREMENT, id_cliente INTEGER, fecha TEXT, 
              libras REAL, precio REAL, total REAL, abono REAL, saldo REAL, estado TEXT)''')
conn.commit()

st.title("🥩 Control de Pedidos y Clientes")

menu = st.sidebar.radio(
    "Menú Principal",
    [
        "1º Ingresar Pedido",
        "2º Ver Cliente",
        "3º Ingresar Pago",
        "4º Agregar / Borrar Cliente",
        "5º Ver Pendientes"
    ]
)

# 1º INGRESAR PEDIDO
if menu == "1º Ingresar Pedido":
    st.header("1º Ingresar Pedido")
    c.execute("SELECT id, nombre FROM clientes")
    clientes_list = c.fetchall()
    
    if not clientes_list:
        st.warning("⚠️ Primero agregue clientes en la opción 4.")
    else:
        opciones_cli = {f"{nombre} (ID: {cid})": cid for cid, nombre in clientes_list}
        cliente_sel = st.selectbox("Seleccione Cliente", list(opciones_cli.keys()))
        id_cli = opciones_cli[cliente_sel]

        libras = st.number_input("Libras de Carne", min_value=0.1, step=0.5, value=1.0)
        precio = st.number_input("Precio por Libra", min_value=0.1, step=1.0, value=1.0)

        if st.button("Guardar Pedido", type="primary"):
            total = libras * precio
            fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
            c.execute("INSERT INTO pedidos (id_cliente, fecha, libras, precio, total, abono, saldo, estado) VALUES (?, ?, ?, ?, ?, 0, ?, 'pendiente')",
                      (id_cli, fecha, libras, precio, total, total))
            conn.commit()
            st.success(f"✅ Pedido guardado el {fecha}. Total: {total:.1f}")

# 2º VER CLIENTE
elif menu == "2º Ver Cliente":
    st.header("2º Ver Cliente")
    c.execute("SELECT id, nombre FROM clientes")
    clientes_list = c.fetchall()
    
    if not clientes_list:
        st.info("No hay clientes registrados.")
    else:
        id_consulta = st.number_input("Ingrese ID del Cliente", min_value=1, step=1)
        if st.button("Buscar"):
            c.execute("SELECT nombre FROM clientes WHERE id=?", (id_consulta,))
            cli = c.fetchone()
            if not cli:
                st.error("⚠️ Cliente no encontrado.")
            else:
                st.subheader(f"Cliente: {cli[0]} (ID: {id_consulta})")
                c.execute("SELECT id, fecha, libras, precio, total, abono, saldo, estado FROM pedidos WHERE id_cliente=? AND estado='pendiente'", (id_consulta,))
                rows = c.fetchall()
                if not rows:
                    st.info("No tiene pedidos pendientes.")
                else:
                    st.table([{
                        "ID Pedido": r[0], 
                        "Fecha": r[1], 
                        "Lbs": f"{r[2]:.1f}", 
                        "Precio/lb": f"{r[3]:.1f}", 
                        "Total": f"{r[4]:.1f}", 
                        "Abono": f"{r[5]:.1f}", 
                        "Saldo": f"{r[6]:.1f}", 
                        "Estado": r[7]
                    } for r in rows])
                    
                    monto_total_pendiente = sum(r[6] for r in rows)
                    st.success(f"💰 **Monto Total Pendiente: {monto_total_pendiente:.1f}**")

# 3º INGRESAR PAGO
elif menu == "3º Ingresar Pago":
    st.header("3º Ingresar Pago")
    c.execute("SELECT p.id, c.nombre, p.saldo FROM pedidos p JOIN clientes c ON p.id_cliente = c.id WHERE p.estado='pendiente'")
    pedidos_pend = c.fetchall()
    
    if not pedidos_pend:
        st.info("No hay pedidos pendientes de pago.")
    else:
        dict_ped = {f"Pedido #{r[0]} - {r[1]} (Saldo: {r[2]:.1f})": (r[0], r[2]) for r in pedidos_pend}
        ped_sel = st.selectbox("Seleccione Pedido", list(dict_ped.keys()))
        id_ped, saldo_actual = dict_ped[ped_sel]
        
        monto = st.number_input("Monto a Abonar", min_value=0.1, max_value=float(saldo_actual), step=1.0)
        
        if st.button("Aplicar Pago", type="primary"):
            nuevo_saldo = saldo_actual - monto
            nuevo_estado = "cancelado" if nuevo_saldo == 0 else "pendiente"
            c.execute("UPDATE pedidos SET abono = abono + ?, saldo = ?, estado = ? WHERE id = ?", (monto, nuevo_saldo, nuevo_estado, id_ped))
            conn.commit()
            if nuevo_saldo == 0:
                st.success(f"🎉 ¡Pedido #{id_ped} pagado por completo!")
            else:
                st.success(f"✅ Abono de {monto:.1f} aplicado. Nuevo saldo: {nuevo_saldo:.1f}")

# 4º AGREGAR / BORRAR CLIENTE
elif menu == "4º Agregar / Borrar Cliente":
    st.header("4º Agregar / Borrar Cliente")
    tab1, tab2 = st.tabs(["Agregar Cliente", "Borrar Cliente"])
    
    with tab1:
        nuevo_id = st.number_input("ID del Cliente", min_value=1, step=1)
        nuevo_nom = st.text_input("Nombre del Cliente")
        if st.button("Guardar Cliente"):
            c.execute("SELECT id FROM clientes WHERE id=?", (nuevo_id,))
            if c.fetchone():
                st.error("⚠️ El ID ya existe.")
            elif not nuevo_nom.strip():
                st.warning("Escriba un nombre.")
            else:
                c.execute("INSERT INTO clientes VALUES (?, ?)", (nuevo_id, nuevo_nom.strip()))
                conn.commit()
                st.success(f"✅ Cliente '{nuevo_nom}' guardado con ID {nuevo_id}.")

    with tab2:
        borrar_id = st.number_input("ID del Cliente a Borrar", min_value=1, step=1)
        if st.button("Borrar Cliente"):
            c.execute("SELECT nombre FROM clientes WHERE id=?", (borrar_id,))
            cli = c.fetchone()
            if cli:
                c.execute("DELETE FROM clientes WHERE id=?", (borrar_id,))
                c.execute("DELETE FROM pedidos WHERE id_cliente=?", (borrar_id,))
                conn.commit()
                st.success(f"🗑️ Cliente '{cli[0]}' eliminado.")
            else:
                st.error("⚠️ ID no encontrado.")

# 5º VER PENDIENTES
elif menu == "5º Ver Pendientes":
    st.header("5º Clientes con Pedidos Pendientes")
    # Consulta agrupada por cliente con la suma de sus saldos pendientes
    c.execute('''SELECT c.id, c.nombre, SUM(p.saldo) 
                 FROM clientes c 
                 JOIN pedidos p ON c.id = p.id_cliente 
                 WHERE p.estado = 'pendiente' 
                 GROUP BY c.id, c.nombre''')
    pendientes = c.fetchall()
    
    if not pendientes:
        st.info("🎉 No hay ninguna deuda pendiente.")
    else:
        # Mostrar la lista con el monto total por cada cliente
        st.table([{
            "ID Cliente": r[0], 
            "Nombre": r[1], 
            "Total Pendiente": f"{r[2]:.1f}"
        } for r in pendientes])
        
        # Calcular y mostrar el gran total de todos los clientes acumulados
        gran_total_pendiente = sum(r[2] for r in pendientes)
        st.success(f"💵 **GRAN TOTAL PENDIENTE GENERAL: {gran_total_pendiente:.1f}**")

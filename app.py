# Rozdelenie do dvoch riadkov pre lepšiu prehľadnosť (3 hore, 2 dole)
      row1_col1, row1_col2, row1_col3 = st.columns(3)
      row2_col1, row2_col2 = st.columns(2)

      with row1_col1:
        st.plotly_chart(
            create_gauge(t_val, "Teplota", 50, "°C", min_val=-20),
            use_container_width=True,
        )
      with row1_col2:
        st.plotly_chart(
            create_gauge(h_val, "Vlhkosť", 100, "%", min_val=0),
            use_container_width=True,
        )
      with row1_col3:
        st.plotly_chart(
            create_gauge(w_val, "Vietor", 50, "km/h", min_val=0),
            use_container_width=True,
        )

      with row2_col1:
        st.plotly_chart(
            create_gauge(r_val, "Zrážky", 50, "mm", min_val=0),
            use_container_width=True,
        )
      with row2_col2:
        st.plotly_chart(
            create_gauge(uv_val, "UV index", 12, "", min_val=0),
            use_container_width=True,
        )
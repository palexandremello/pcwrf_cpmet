'''
Script que plota um mapa mostrando posicionamento das estações do INMET
e dos pontos de grade dos quais se obtém as séries temporais das
previsões por conjunto

Mateus S. Teixeira, julho/2020
'''
import netCDF4 as nc
import numpy as np
import wrf
import pandas as pd
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt


# coordenadas estações meteorológicas do INMET
cidades=[['Bagé',-31.33,-54.10],['Canela',-29.36,-50.81],['Canguçu',-31.40,-52.68],
         ['Caxias do Sul',-29.16,-51.18],['Frederico Westphalen',-27.36,-53.40],
         ['Iraí',-27.20,-53.25],['Passo Fundo',-28.26,-52.41],['Pelotas',-31.76,-52.34],
         ['Porto Alegre',-30.03,-51.21],['Rio Grande',-32.03,-52.11],
         ['Santa Maria',-29.69,-53.81],['Santa Vitória do Palmar',-33.53,-53.37],
         ['São Luiz Gonzaga',-28.41,-54.96],['Torres',-29.33,-49.73],
         ['Uruguaiana',-29.76,-57.09] ]
estacoes_met=pd.DataFrame( cidades, columns=['cidade','lat','lon'] )  # tabela com coordenada das estações

# usando um arquivo da PCWRF para obter pontos de grade
arq = nc.Dataset( '../saidas/20200520_00/membro01/wrfout_d01_2020-05-20_00' )

# obtendo pontos de grade mais próximos das coordenadas LON,LAT fornecidas
# estacoes_met_wrf[0,...] -> valores X (oeste-leste)
# estacoes_met_wrf[1,...] -> valores Y (sul-norte)
estacoes_met_wrf = wrf.ll_to_xy( arq,                 # coordenadas (X,Y) das estações INMET
                                 estacoes_met.iloc[:,1].tolist(),
                                 estacoes_met.iloc[:,2].tolist() )

# obtendo LON,LAT dos pontos de grade obtidos acima
# lat_lon_gridpoints[0,...] -> valores latitude
# lat_lon_gridpoints[1,...] -> valores longitude
lat_lon_gridpoints = wrf.xy_to_ll( arq,
                                 estacoes_met_wrf[0,:],
                                 estacoes_met_wrf[1,:] )


# criando mapa com pontos de grade usados para extração e coordenadas das estações INMET
projWRF = wrf.get_cartopy( wrfin=arq )
estados = cfeature.NaturalEarthFeature(category='cultural', scale='50m',
                                       facecolor='none', name='admin_1_states_provinces_shp')

# limites X e Y das coordenadas projetadas
xlims = wrf.cartopy_xlim( wrfin=arq )
ylims = wrf.cartopy_ylim( wrfin=arq )

# criando gráfico
ax = plt.axes( projection=projWRF )
ax.coastlines( '50m', linewidth=0.8 )
ax.gridlines( color='black', linestyle='dotted' )
ax.add_feature( estados, linewidth=0.5, edgecolor='black' )

# obtendo domínio em torno do estado do RS
RS = wrf.GeoBounds( wrf.CoordPair( lat=-35.0,lon=-60.0 ),
                    wrf.CoordPair( lat=-26.0,lon=-48.0 ) )
ax.set_xlim( wrf.cartopy_xlim( wrfin=arq, geobounds=RS )  )
ax.set_ylim( wrf.cartopy_ylim( wrfin=arq, geobounds=RS )  )
ax.set_title( 'Comparação INMET (vermelho) x WRF (verde)\n PCWRF/CPMet/FAMET/UFPel' )

# adicionando pontos das estações INMET
ax.scatter( estacoes_met.iloc[:,2].tolist(), estacoes_met.iloc[:,1].tolist(),
             marker='o', color='red', transform=ccrs.PlateCarree(), label='INMET' )
# adicionando pontos de grade das extrações
ax.scatter( lat_lon_gridpoints[1,:], lat_lon_gridpoints[0,:],
             marker='^', color='green', transform=ccrs.PlateCarree(), label='WRF' )
# legenda
ax.legend( loc='upper left', fontsize='large' )

plt.savefig( 'Mapa_estacoes_ptsGrade.png', dpi=150 )
plt.close()


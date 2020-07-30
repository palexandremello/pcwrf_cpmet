import netCDF4 as nc
import numpy as np
from datetime import datetime as dt   # manipulação de datas
from datetime import timedelta        # operação com datas
import wrf
import xarray as xr
import os
import cartopy.crs as ccrs
import cartopy.feature as cfeature
import matplotlib.pyplot as plt
import matplotlib.colors


# listagem dos arquivos
listaPrev = os.listdir( '../saidas/' )
listaPrev.sort()     # ordenando a lista de arquivos
iniPrev = dt.strptime( listaPrev[-1], '%Y%m%d_%H' )
dataDir = '../saidas/'+listaPrev[-1]
listaArqsFcst = os.listdir( dataDir+'/membro01' )
nArqs = len(listaArqsFcst)    # quantidade de arquivos = quantidade de dias
preNomeArqPrev = 'wrfout_d01_'
strIniPrev = str( iniPrev.year ) + '-' +\
    str( iniPrev.month ).zfill(2) + '-' +\
    str( iniPrev.day ).zfill(2) + 'T' +\
    str( iniPrev.hour ).zfill(2)


# cores e mapa de cores para Desvio Padrão (similar ao ensemble do ECMWF)
cores = ['lawngreen','limegreen','forestgreen','green','white','plum','mediumorchid','fuchsia','magenta','orchid']
limites = [ 0, 0.2, 0.4, 0.6, 0.8, 1.2, 1.8, 2.5, 5, 8, 15 ]
mapa_cores =  matplotlib.colors.ListedColormap( cores )
mapa_cores_norma = matplotlib.colors.BoundaryNorm( limites, mapa_cores.N )


# LOOP dos dias de previsão
for deltaDia in range(0,nArqs):

    # dia da previsão analisada
    diaPrev = iniPrev + timedelta( days=deltaDia )
    strDiaPrev = str( diaPrev.year ) + '-' +\
        str( diaPrev.month ).zfill(2) + '-' +\
        str( diaPrev.day ).zfill(2) + '_' +\
        str( diaPrev.hour ).zfill(2)
    
    # cada dia de previsão consta em um arquivo
    print('Previsões para o dia '+strDiaPrev )
    
    # definindo o nome do arquivo a ser lido de cada membro
    arqPrev = preNomeArqPrev + strDiaPrev

    # varrendo os arquivos e copiando previsões
    #   vai EXISTIR UM LOOP INTERNO COM OS DIAS DIFERENTES
    #       POIS OS ARQUIVOS ESTAO SEPARADOS POR DIA
    #
    print( '\t Acessando arquivos ...')
    for membro in range(0,20):
    
        # definindo o membro do qual se obterá as previsões
        dirArq = dataDir+'/membro'+str(membro+1).zfill(2)+'/' # zfill preenche esquerda com zeros, 2 dígitos
        
        if membro == 0:
            #print( '\t acessando membro 1' )
            arq = nc.Dataset( dirArq+arqPrev )

            chuvac = wrf.getvar( arq, 'RAINC', wrf.ALL_TIMES )
            chuvanc = wrf.getvar( arq, 'RAINNC', wrf.ALL_TIMES )
            varMet = chuvac+chuvanc
            varMet = varMet.rename( 'chuva' )

            tempoPrev = wrf.getvar( arq, 'times', wrf.ALL_TIMES )
            projecaoWRF = wrf.get_cartopy( wrfin=arq )    # projeção dos dados -> para plotagem
            dominioLimsX = wrf.cartopy_xlim( wrfin=arq )
            dominioLimsY = wrf.cartopy_ylim( wrfin=arq )

            arq.close()

        else:

            #print( '\t acessando membro '+str( membro+1 ) )
            arq = nc.Dataset( dirArq+arqPrev )

            chuvac = wrf.getvar( arq, 'RAINC', wrf.ALL_TIMES )
            chuvanc = wrf.getvar( arq, 'RAINNC', wrf.ALL_TIMES )
            d2 = chuvac+chuvanc
            del chuvac, chuvanc

            arq.close()
            
            d3 = xr.concat( [ varMet, d2 ], dim='membro' )

            # apagando variáveis que serão renovadas
            # e guardando união na variável de interesse
            del varMet, d2
            varMet = d3.copy()
            del d3

    # atribuindo coordenadas para os membros
    varMet = varMet.assign_coords( membro=range(1,21) )
    if len( varMet.shape ) < 4:
        nmembros, nlat, nlon = varMet.shape
    else:
        nmembros, nt, nlat, nlon = varMet.shape

        # campos médios e de dispersão
    varMet_media = varMet.mean( dim='membro' )
    varMet_dp    = varMet.std( dim='membro' )

    # criando strings de tempo (p/ gráficos)
    strTempoPrev = np.datetime_as_string( tempoPrev, unit='h' )

    # obtendo informações de coordenadas dos dados
    # devem ser usadas antes de qualquer conversão de unidades ou operação
    # aritmética
    lats, lons = wrf.latlon_coords( varMet )
        
    # estados do Brasil
    estados = cfeature.NaturalEarthFeature(category='cultural', scale='50m',
                                           facecolor='none', name='admin_1_states_provinces_shp')
    
    if len( varMet.shape ) < 4:
        nt = 1
    
    # loop sobre os instantes de tempo do arquivo
    for tPrev in range( 0, nt ):
        print( '\t\t Resultados para '+strTempoPrev[ tPrev ] )
        ax = plt.axes( projection=projecaoWRF )
            
        if nt==1:
            campo1 = ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( varMet_media[ :, :] ), colors='black',
                                 levels=np.arange(0,100,5), linewidths=2., transform=ccrs.PlateCarree() )
            plt.clabel( campo1, fmt='%1.0f' )
            
            campo2 = ax.contourf( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( varMet_dp[ :, :] ),
                                  levels=limites, extend='neither', cmap=mapa_cores, norm=mapa_cores_norma,
                                  transform=ccrs.PlateCarree() )
            
        else:
            campo1 = ax.contour( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( varMet_media[ tPrev, :, :] ), colors='black',
                                 levels=np.arange(0,100,5), linewidths=2., transform=ccrs.PlateCarree() )
            plt.clabel( campo1, fmt='%1.0f' )
            
            campo2 = ax.contourf( wrf.to_np(lons), wrf.to_np(lats), wrf.to_np( varMet_dp[ tPrev, :, :] ),
                                  levels=limites, extend='neither', cmap=mapa_cores, norm=mapa_cores_norma,
                                  transform=ccrs.PlateCarree() )
            

        plt.colorbar( campo2, ticks=limites, norm=mapa_cores_norma, boundaries=[0]+limites+[15] )
        ax.coastlines( '50m', linewidth=0.8 )
        ax.set_title('Média (contorno) e DP (colorido) - Chuva acumulada [mm] \n PCWRF/CPPMet/FAMET/UFPel \n Início: '+strIniPrev+' Validade: '+strTempoPrev[ tPrev ] )
        ax.set_xlim( dominioLimsX )
        ax.set_ylim( dominioLimsY )
        ax.gridlines( color='black', linestyle='dotted')
        ax.add_feature( estados, linewidth=.5, edgecolor='black' )
        plt.savefig( 'chuva_media_dp_'+strIniPrev+'_'+strTempoPrev[ tPrev ]+'.png' )
        plt.close()



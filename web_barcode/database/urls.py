from django.urls import path

from . import views

urlpatterns = [
     path('', views.database_home, name='database_home'),
     path('create', views.create, name='create'),
     path('<int:pk>',
          views.DatabaseDetailView.as_view(),
          name='database_detail'
          ),
     path('<int:pk>/update',
          views.DatabaseUpdateView.as_view(),
          name='database_update'
          ),
     path('<int:pk>/delete',
          views.DatabaseDeleteView.as_view(),
          name='database_delete'
          ),
     path('stock/',
          views.database_stock,
          name='database_stock'
          ),
     path('stock-create',
          views.create_stock,
          name='createstock'
          ),
     path('stock/<str:article_marketplace>',
          views.DatabaseStockDetailView.as_view(),
          name='stock_detail'
          ),
     path('stock/<int:pk>/update',
          views.DatabaseStockUpdateView.as_view(),
          name='stock_update'
          ),
     path('stock/<int:pk>/delete',
          views.DatabaseStockDeleteView.as_view(),
          name='stock_delete'
          ),

     path('stock-wb/',
          views.database_stock_wb,
          name='stock-wb'
          ),
     path('createshelving',
         views.create_shelving_stocks,
         name='createshelving'
         ),
     path('stock-shelving/',
          views.database_stock_shelving,
          name='stock-shelving'
          ),
     path('stock-shelving/<int:pk>',
          views.DatabaseShelvingUpdateView.as_view(),
          name='stock-shelving-update'
          ),

     path('sales/',
          views.database_sales,
          name='database_sales'
          ),
     path('sales-create',
          views.create_sales,
          name='createsales'
          ),
     path('sales/<str:article_marketplace>',
          views.DatabaseSalesDetailView.as_view(),
          name='sales_detail'
          ),
     path('sales/<int:pk>/update',
          views.DatabaseSalesUpdateView.as_view(),
          name='sales_update'
          ),
     path('sales/<int:pk>/delete',
          views.DatabaseSalesDeleteView.as_view(),
          name='sales_delete'
          ),
     path('export/',
          views.export_movies_to_xlsx,
          name='export'
          ),
     path('login/', views.LoginUser.as_view(), name='login'),
     path('logout/', views.logout_user, name='logout'),
]

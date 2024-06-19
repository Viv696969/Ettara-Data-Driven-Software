from django.shortcuts import render
from django.contrib.auth.models import User
from rest_framework.permissions import IsAuthenticated,AllowAny
from rest_framework.decorators import api_view,permission_classes
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken,AccessToken
from .models import *
from django.shortcuts import get_object_or_404
from .serializers import *
import json
from .apps import StoreConfig
import numpy as np

collection=StoreConfig.collection
# Create your views here.

@api_view(['POST'])
@csrf_exempt
def show_categories(request):
    cats=Category.objects.all()
    for cat in cats:
        print(cat.name)

    serializer=CategorySerializer(cats,many=True)
    return JsonResponse({
        'categories':serializer.data
    },status=200)


@api_view(['POST'])
@csrf_exempt
def show_products(request):
    user=request.user
    if user.is_authenticated:
        '''
        do something like recommendation...
        '''
        if 'activity' in request.data:
            '''
            give recommendation based on activity...
            '''
            activity_list=json.loads(
                json.dumps(request.data)
                )['activity']
            
            data=collection.get(
                ids=activity_list,
                include=['embeddings']
            )['embeddings']

            target_embedding=np.array(data).mean(0).tolist()

            ids=list(map(int,collection.query(
                query_embeddings=[target_embedding],
                include=['distances'],
                n_results=5
            )['ids'][0]))[::-1]
            print(ids)
            prods=Product.objects.filter(id__in=ids)
            recommended_products=sorted(
                prods,
                key=lambda x : ids.index(x.id)
            )
            data=RecommendedProductSerializer(recommended_products,many=True).data

            return JsonResponse({'data':data},status=200)
        else:
            products=Product.objects.all()
            data=AllProductSerializer(products,many=True).data

            return JsonResponse({
                'data':data
            },
            status=200
            ) 
    else:
        '''
        Just show the Products..
        '''
        products=Product.objects.all()
        data=AllProductSerializer(products,many=True).data

    return JsonResponse({
        'data':data
    },
    status=200
    )

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def add_to_cart(request):
    user=request.user
    id=int(request.POST['product_id'])
    quantity=int(request.POST['quantity'])
    cart,created=Cart.objects.get_or_create(user=user,product=Product.objects.get(id=id))
    if created:
        cart.quantity=quantity
        cart.total_price=quantity*cart.product.price
        cart.save()
        return JsonResponse({
            'mssg':f'Product {cart.product.name} added to cart..with quantity={quantity}','status':1
        },status=200)
    else:
        return JsonResponse(
            {'mssg':'Product Already In Cart...','status':0},status=200
        )

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def remove_from_cart(request):
    try:
        product_id=int(request.POST['product_id'])
        product=Product.objects.get(id=product_id)
        mssg=f"{product.name} Removed from Cart"
        cart=Cart.objects.filter(user=request.user,product=product).first()
        cart.delete()
        return JsonResponse({
            'mssg':mssg,
        },status=200)
    except:
        return JsonResponse({'mssg':f'error finding product in cart..'},status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def show_cart(request):
    user=request.user
    cart=Cart.objects.filter(user=user)
    cart_size=len(cart)
    if cart_size>0:
        data=CartSerializer(cart,many=True).data
        return JsonResponse({
            'quantity':cart_size,
            'data':data,
        },status=200)

    else:
        return JsonResponse({
            'quantity':cart_size,
        })

@api_view(['POST'])
@csrf_exempt
@permission_classes([IsAuthenticated])
def change_quantity(request):
    type_of_change=request.POST['type']
    quantity=int(request.POST['quantity'])
    id=int(request.POST['product_id'])
    cart=Cart.objects.filter(user=request.user,product__id=id).first()
    if type_of_change=='reduce':
        cart.quantity=cart.quantity-quantity
    else:
        if cart.product.qty<cart.quantity+quantity:
            return JsonResponse({
                'mssg':f'Only {cart.product.qty} {cart.product.name} left in stock..',
                'status':False
            })
        cart.quantity=cart.quantity+quantity
    cart.total_price=cart.quantity*cart.product.price
    cart.save()
    return JsonResponse(
        {
        'mssg':f'Quantity changed for {cart.product.name}',
        'status':True
        }
        )


# @api_view(["GET"])
# def test(request):
#     client=chromadb.PersistentClient("./store_db")
#     collection=client.get_or_create_collection("store_collection",  metadata={"hnsw:space": "cosine"}) 

#     from .models import Product,Category
#     products=Product.objects.all()
#     print(products)
#     documents=[]
#     metadatas=[]
#     ids=[]
#     for product in products:
#         documents.append(
#             product.name+product.description
#         )
#         metadatas.append({"category":product.category.name})
#         ids.append(str(product.id))

#     collection.add(
#     documents=documents,
#     metadatas=metadatas,
#     ids=ids
# )
#     return JsonResponse(
#         {
#             'data':'stored...'
#         }
#     )
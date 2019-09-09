from django.contrib.auth.models import User
from rest_framework import viewsets, mixins
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticatedOrReadOnly, \
    IsAuthenticated
from rest_framework.response import Response

from .permissions import IsOwner
from .serializers import UserSerializer, PostSerializer, VoteSerializer

from teste.models import Post, Vote


class NoModifyModelViewSet(mixins.CreateModelMixin,
                           mixins.RetrieveModelMixin,
                           mixins.DestroyModelMixin,
                           mixins.ListModelMixin,
                           viewsets.GenericViewSet):
    pass


class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    @action(methods=['GET'], detail=False)
    def me(self, request, *args, **kwargs):
        self.kwargs.update(pk=request.user.id)
        return self.retrieve(request, *args, **kwargs)


class PostViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Post.objects.all().order_by('-created_on')
    serializer_class = PostSerializer
    permission_classes = [IsOwner]

    @action(methods=['POST'], detail=True,
            permission_classes=[IsAuthenticated])
    def like(self, request, pk, *args, **kwargs):
        return self._vote(request, pk, 1)

    @action(methods=['POST'], detail=True,
            permission_classes=[IsAuthenticated])
    def dislike(self, request, pk=None, *args, **kwargs):
        return self._vote(request, pk, -1)

    def _vote(self, request, pk, vote):
        post = self.get_object()
        vote = Vote.objects.create(content_object=post, vote=vote,
                                   author=request.user)
        return Response(
            VoteSerializer(vote, context=self.get_serializer_context()).data
        )


class VoteViewSet(NoModifyModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = Vote.objects.all().order_by('-created_at')
    serializer_class = VoteSerializer
    permission_classes = [IsOwner]


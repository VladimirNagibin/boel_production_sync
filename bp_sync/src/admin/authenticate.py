from fastapi import HTTPException, Request, status
from jose import jwt
from jose.exceptions import JWTError
from sqladmin.authentication import AuthenticationBackend

from core.logger import logger
from core.settings import settings


class BasicAuthBackend(AuthenticationBackend):  # type: ignore
    def __init__(
        self,
        username: str = settings.USER_ADMIN,
        password: str = settings.PASS_ADMIN,
        secret_key: str = settings.SECRET_KEY,
    ):
        super().__init__(secret_key)
        self.username = username
        self.password = password
        self.secret_key = secret_key

    async def login(self, request: Request) -> bool:
        """
        Verifying user credentials.
        """
        form = await request.form()
        username = form.get("username")
        password = form.get("password")

        if username != self.username or password != self.password:
            logger.info("Access verification is not successful.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
                headers={"WWW-Authenticate": "Basic"},
            )
        logger.info("Access verification is successful.")

        # JWT token generation
        token = jwt.encode(
            {"sub": username},
            self.secret_key,
            algorithm=settings.ALGORITHM,
        )

        # Saving token in the session
        request.session.update({"token": token})
        return True

    async def logout(self, request: Request) -> bool:
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        token = request.session.get("token")

        if not token:
            return False

        try:
            payload = jwt.decode(
                token, self.secret_key, algorithms=[settings.ALGORITHM]
            )
        except JWTError:
            return False
        username = payload.get("sub")
        return bool(username == self.username)

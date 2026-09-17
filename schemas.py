from pydantic import BaseModel , ConfigDict , Field ,EmailStr
from datetime import datetime




class UserBase(BaseModel):
    username: str = Field(min_length=1 , max_length=20)
    email : EmailStr = Field(max_length=100)


class UserCreate(UserBase):
    pass


class UserResponse(UserBase):
    model_config = ConfigDict(from_attributes=True)

    id : int
    image_file: str | None
    image_path : str


class UserUpdate(BaseModel):

    username : str | None = Field(default=None , min_length=1 , max_length=20)
    email : str | None = Field(default= None , max_length=120)
    image_file : str | None = Field(default=None , min_length=1 , max_length=50)



class PostBase(BaseModel):
    title: str  = Field(min_length= 1, max_length=100)
    content: str = Field(min_length= 1 )
    # author: str = Field(min_length=1, max_length=50)


class PostCreate(PostBase):
    user_id : int


class PostUpdate(BaseModel):
    title : str | None = Field(default=None , min_length= 1, max_length= 100)
    content : str | None = Field(default= None , min_length=1)

class PostResponse(PostBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date_posted: datetime
    author: UserResponse

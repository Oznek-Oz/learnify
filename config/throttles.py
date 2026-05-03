from rest_framework.throttling import UserRateThrottle


class CourseUploadThrottle(UserRateThrottle):
    scope = 'course_upload'


class GenerationThrottle(UserRateThrottle):
    scope = 'generation'

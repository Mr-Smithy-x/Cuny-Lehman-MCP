
def reduce_course_detail_response(content: dict):
    if "sections" in content:
        sections = content['sections']
    else:
        sections = []

    if "professors" in content:
        professors = content['professors']
    else:
        professors = []

    if "rooms" in content:
        rooms = content['rooms']
    else:
        rooms = []

    shrunk_sections = []
    for section in sections:
        campus = section['campus']
        id = section['id']
        career = section['career']
        courseCode = section['courseCode']
        courseMaterials = section['courseMaterials']
        department = section['department']
        linkedSections = section['linkedSections']
        notesList = section['notesList']
        sectionName = section['sectionName']
        credits = section['maxCreditHours']
        sectionNumber = section['sectionNumber']
        status = section['status']
        times = section['times']
        startDate = section['startDate']
        endDate = section['endDate']
        textBook = section['customFields']['ssrClsTxbText'] if 'customFields' in section and 'ssrClsTxbText' in section['customFields'] else None
        shrunk_sections.append({
            'id': id,
            'credits': credits,
            'campus': campus,
            'career': career,
            'courseCode': courseCode,
            'textBook': textBook,
            'courseMaterials': courseMaterials,
            'department': department,
            'linkedSections': linkedSections,
            'notesList': notesList,
            'sectionName': sectionName,
            'sectionNumber': sectionNumber,
            'status': status,
            'times': times,
            'startDate': startDate,
            'endDate': endDate
        })

    return {
        'sections': shrunk_sections,
        'professors': professors,
        'rooms': rooms,
    }


def reduce_search_response(course_info: dict):
    courses = []
    for data in course_info['data']:
        result = {
            'id': data['id'],
            'name': data['name'],
            'longName': data['longName'],
            'requirementDesignation': data['requirementDesignation'],
            'scheduleDisplayName': data['scheduleDisplayName'],
            'campus': data['campus'],
            'career': data['career'],
            'code': data['code'],
            'courseTypicallyOffered': data['courseTypicallyOffered'],
            'courseApproved': data['courseApproved'],
            'courseGroupId': data['courseGroupId'],
            'credits': data['credits']['numberOfCredits'],
            'departments': data['departments'],
            'dependents': data['dependents'],
            'description': data['description'],
            'consent': data['consent'],
            'gradeMode': data['gradeMode'],
            'gradedComponent': data['gradedComponent'],
            'sisId': data['sisId'],
            'rawCourseId': data['customFields']['rawCourseId'],
        }
        courses.append(result)
    return courses
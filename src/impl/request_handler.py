
# src/impl/request_handler.py

# central dispatch layer

# from models.upload_and_process_pdf200_response import UploadAndProcessPdf200Response

from typing import Optional


import os
import sys
from pathlib import Path



script_dir = os.path.dirname(__file__)
sys.path.append(script_dir)  # Appe

# sys.path.append(str(Path(__file__).resolve().parent.parent / "llmec"))
# print("syspath>", sys.path)


# from celery_app import async_text_to_image_service
# from models.bug_report_request import BugReportRequest
from collections import OrderedDict
# from models.operation_status import OperationStatus

import logging
logger = logging.getLogger(__name__)



# handle_get_all_files
# handle_get_all_files_with_pagination


# def verify_user_id(user_id: int, db: Session) -> User:
#     """
#     Verifies the user_id by checking the database.
#
#     :param user_id: The user ID extracted from the JWT token.
#     :param db: The database session.
#     :return: The User object if the user exists and is valid.
#     :raises HTTPException: If the user_id is not valid or does not exist.
#     """
#     user = db.query(User).filter(User.id == user_id).first()
#
#     if not user:
#         raise HTTPException(status_code=401, detail="Invalid user ID or user does not exist")
#
#     if not user.is_active:  # Assuming you have an 'is_active' flag in your User model
#         raise HTTPException(status_code=401, detail="User account is inactive")
#
#     return user


class RequestHandler:
    #def __init__(self, iie,ch, et=False):
    def __init__(self, app):
        self.app = app
        self.package_content = None
        self.requester_id = None
        self.package_sent_time = None
        self.response = None
        # self.iie=iie
        # self.ch=ch
        self.DATA_IS_VALID = None
        self.META_IS_VALID = None
        self.USER_HAS_PERMISSION = None

        self.REQUEST_IS_VALID=None
        self.error_code=None

        # logger = logging.getLogger(__name__)
        #
        # logger.setLevel(logging.DEBUG)
        logger.debug("Request Handler ")
        self.logger= logger

        #self.elapsed_time =et
        self.elapsed_time=None
        if not self.elapsed_time:

            self.elapsed_time= OrderedDict()

        # self.elapsed_time = OrderedDict()

        # self.elapsed_time["start_time"] = time.time()
    def op_validity(self,meta_data):

        is_permitted=self.check_metadata_validity(meta_data)
        if is_permitted:
            return True
        else:
           # raise HTTPException(status_code=400, detail="user doesnt have permission for this operation")
            return False

    def check_metadata_validity(self, meta_data):
        return True

    # def handle_run_categorisation_for_file(self, user_id: int, file_id: int):
    #     try:
    #         # Update the process start time
    #         self.update_initial_data_status(file_id, user_id, status="in progress", started_at=get_current_time())
    #
    #         # Perform the categorization (This is the long-running process)
    #         result = self.categorize_file(user_id, file_id)
    #
    #         # On successful categorization, update status to 'completed'
    #         self.update_initial_data_status(file_id, user_id, status="completed", percentage=100,
    #                                         completed_at=get_current_time())
    #
    #     except Exception as e:
    #         # If there's an error, update the status to 'failed'
    #         self.update_initial_data_status(file_id, user_id, status="failed")
    #         logger.error(f"Categorization failed for file_id {file_id}: {str(e)}", exc_info=True)
    #


    def handle_get_bank(self, country, supported):

        class MyRequest:
            def __init__(self):
                self.country = country
                self.supported = supported

        mr = MyRequest()

        from impl.services.data.bank_info_retriever_service import BankInfoRetrieverService
        dependency = self.app.state.services

        p = BankInfoRetrieverService(mr, dependencies=dependency)
        return p.response

    def handle_get_records_paginated(self,
                                     user_id: int,
                                     document_id: Optional[int],
                                     start_date: Optional[str],
                                     end_date: Optional[str],
                                     associated_with: Optional[str],
                                     limit: int,
                                     offset: int ,
                                     sort_by,
                                     order,
                                     min_amount, 
                                     max_amount,
                                     currency,
                                     keyword_search,
                                     exact_match,
                                     by_category,
                                     by_subcategory,
                                     bring_cleaned_text,
                                     bring_not_vetted,
                                     bring_tax_deductible,
                                     bring_failed_to_categorize) :

        from impl.services.record.records_retriever_with_pagination_service import RecordsRetrieverWithPaginationService
        dependency = self.app.state.services

    
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.document_id = document_id
                self.start_date = start_date
                self.end_date = end_date
                self.associated_with = associated_with
                self.limit = limit
                self.offset = offset
                self.sort_by=sort_by
                self.order=order
                self.min_amount=min_amount
                self.max_amount=max_amount
                self.currency=currency
                                
                self.keyword_search=keyword_search
                self.exact_match=exact_match
                self.by_category=by_category
                self.by_subcategory=by_subcategory
                self.bring_cleaned_text=bring_cleaned_text
                self.bring_not_vetted=bring_not_vetted
                self.bring_tax_deductible=bring_tax_deductible
                self.bring_failed_to_categorize=bring_failed_to_categorize

        mr = MyRequest()
        p = RecordsRetrieverWithPaginationService(mr, dependencies=dependency)
        return p.response




    def handle_get_records(self, user_id,document_id, start_date,end_date,  associated_with):



        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.document_id = document_id
                self.start_date = start_date
                self.end_date = end_date
                self.associated_with = associated_with

        from impl.services.record.records_retriever_service import RecordsRetrieverService
        dependency = self.app.state.services

        mr = MyRequest()
        p = RecordsRetrieverService(mr, dependencies=dependency)
        return p.response



    def handle_delete_file(self, user_id, delete_records, file_id):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.delete_records = delete_records
                self.file_id = file_id

        from impl.services.file.file_eraser_service import FileEraserService
        dependency = self.app.state.services

        mr = MyRequest()
        p = FileEraserService(mr, dependency)
        return p.response

    def handle_delete_record(self,user_id,record_id ):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.record_id = record_id

        from impl.services.record.record_eraser_service import RecordEraserService
        dependency = self.app.state.services

        mr = MyRequest()
        p = RecordEraserService(mr, dependencies=dependency)
        return p.response

    def handle_add_records(self,user_id, create_record_data ):


        from impl.services.record.record_creator_service import RecordCreatorService
        dependency = self.app.state.services

        p = RecordCreatorService(create_record_data, user_id=user_id, dependencies=dependency)
        return p.response


    def handle_get_all_files_with_pagination(self, user_id, limit, offset,  bank_name):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.bank_name = bank_name
                self.limit = limit
                self.offset = offset


        mr = MyRequest()

        from impl.services.file.file_retriever_with_pagination_service import FileListPaginationRetriever
        dependency = self.app.state.services

        p = FileListPaginationRetriever(mr, dependency)
        return p.response



    def handle_yearly_overview(self, user_id, year):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.year = year

        mr = MyRequest()

        from impl.services.file.yearly_overview_service import YearlyOverviewService
        dependency = self.app.state.services

        p = YearlyOverviewService(mr, dependency)

        
        return p.response
    def handle_get_all_files(self, user_id, bank_name):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.bank_name = bank_name

        mr = MyRequest()

        from impl.services.file.file_retriever_service import FileListRetriever
        dependency = self.app.state.services

        p = FileListRetriever(mr, dependency)
        return p.response


    def handle_create_family(self,  user_id, create_family_group_request):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.family_name = create_family_group_request.family_name

        mr = MyRequest()
        from impl.services.family.family_management import FamilyCreator
        p = FamilyCreator(mr)
        return p.response


    def handle_change_category(self,user_id, RecordData):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.category = RecordData.category
                self.subcategory = RecordData.subcategory
                self.record_id = RecordData.record_id

                self.is_active = RecordData.is_active
                self.backup_category = RecordData.backup_category
                self.backup_subcategory = RecordData.backup_subcategory
                self.apply_to_similar_records = RecordData.apply_to_similar_records

        mr = MyRequest()
        from impl.services.record.record_category_updater_service import RecordCategoryUpdaterService
        dependency = self.app.state.services
        p=RecordCategoryUpdaterService(mr, dependencies=dependency)
        return p.response
    

    
    
    
    def handle_monthly_freq_report(self, user_id, bank_account_id, start_date, end_date):
        
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.bank_account_id = bank_account_id
                self.start_date = start_date
                self.end_date = end_date

        from impl.services.report.create_a_historical_freq_report_service import CreateAHistoricalFreqReportService
        dependency = self.app.state.services

        mr = MyRequest()
        p = CreateAHistoricalFreqReportService(mr, dependencies=dependency)
        return p.response
    


   


    def handle_get_users_list(self,page, page_size, country,  user_id,email,sort_by, sort_order ):

        class MyRequest:
            def __init__(self):
                self.page = page
                self.page_size = page_size
                self.country = country
                self.user_id = user_id
                self.email = email
                self.sort_by = sort_by
                self.sort_order = sort_order

        
        from impl.services.admin.get_users_list_service import GetUsersListService
        dependency = self.app.state.services

        mr = MyRequest()
        p = GetUsersListService(mr, dependencies=dependency)
        return p.response
    

    
    
    def handle_upload_file_snapshot(self,user_id, body ):
        
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.body = body
            
        
        from impl.services.file.upload_file_snapshot_service import UploadFileSnapshotService
        dependency = self.app.state.services
        
        mr = MyRequest()
        p = UploadFileSnapshotService(mr, dependencies=dependency)
        return p.response

    def handle_get_file_snapshot(self,user_id, file_id ):
        
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.file_id = file_id
            
        
        from impl.services.file.get_file_snapshot_service import GetFileSnapshotService
        dependency = self.app.state.services
        
        mr = MyRequest()
        p = GetFileSnapshotService(mr, dependencies=dependency)
        return p.response
    
    def handle_custom_report(self,user_id, get_custom_report_request ):
        searches = get_custom_report_request.searches
        start_date = get_custom_report_request.start_date
        end_date = get_custom_report_request.end_date
        currency = get_custom_report_request.currency

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
             #   self.get_custom_report_request = get_custom_report_request
                self.searches = searches
                self.start_date = start_date
                self.end_date = end_date
                self.currency = currency
            
        
        from impl.services.report.create_a_custom_report_service import CreateACustomReportService
        dependency = self.app.state.services
        
        mr = MyRequest()
        p = CreateACustomReportService(mr, dependencies=dependency)
        return p.response
    
    
    def handle_periodic_report(self, user_id, paradigm, period_type, bank_account_id, currency, start_date, end_date):
        
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.paradigm = paradigm
                self.period_type = period_type
                self.bank_account_id = bank_account_id
                self.currency = currency
                self.start_date = start_date
                self.end_date = end_date

        from impl.services.report.create_a_periodic_report_service import CreateAPeriodicReportService
        dependency = self.app.state.services

        mr = MyRequest()
        p = CreateAPeriodicReportService(mr, dependencies=dependency)
        return p.response



    def handle_scatter_report(self, user_id, category, subcategory, start_date,end_date,  currency,  bank_account_id):


        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.category = category
                self.subcategory = subcategory
                self.start_date = start_date
                self.end_date = end_date
                self.currency = currency
                self.bank_account_id = bank_account_id

        from impl.services.report.create_a_scatter_report_service import CreateAScatterReportService
        dependency = self.app.state.services


        mr = MyRequest()
        p = CreateAScatterReportService(mr, dependencies=dependency) # from impl.services.report_management import ReportMaker, HistoricalReportMaker
        return p.response


    #this is inside request_handler.py
    def handle_piechart_report(self, user_id, start_date, end_date, currency, bank_account_id):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.bank_account_id = bank_account_id
                self.start_date = start_date
                self.end_date = end_date
                self.currency = currency

        from impl.services.report.create_a_piechart_report_service import CreateAPiechartReportService
        dependency = self.app.state.services

        mr = MyRequest()
        p = CreateAPiechartReportService(mr, dependencies=dependency) # from impl.services.report_management import ReportMaker, HistoricalReportMaker
        return p.response

    def handle_split_record(self, user_id, record_id, split_record_request):

        class MyRequest:
            def __init__(self):
                self.record_id = record_id
                self.user_id = user_id
                self.splits = split_record_request.splits

        # splits: Optional[List[SplitRecordDTO]]

        dependency = self.app.state.services

        from impl.services.record.record_splitter_service import RecordsSplitterService
        mr = MyRequest()
        p = RecordsSplitterService(mr, dependencies=dependency)
        return p.response

    def handle_file_status(self,user_id,file_id ):

        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.file_id = file_id

        from impl.services.file.file_status_retriver_service import FileStatusRetrieverService
        dependency = self.app.state.services

        mr = MyRequest()
        p = FileStatusRetrieverService(mr,dependency)
        return p.response

    def handle_run_categorisation_for_file_async(self, user_id, file_id):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.file_id = file_id

        from impl.services.file.file_records_categorization_service import FileRecordsCategorizerService
        dependency = self.app.state.services

        mr = MyRequest()
        p = FileRecordsCategorizerService(mr, dependency)

        return p.response

    def handle_run_categorisation_for_file(self, user_id, file_id):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.file_id = file_id

        from impl.services.file.file_records_categorization_service import FileRecordsCategorizerService
        dependency = self.app.state.services

        mr = MyRequest()
        p = FileRecordsCategorizerService(mr,dependency )
        return p.response

    def handle_register(self, auth_register_post_request):

        from impl.services.auth.register_service import RegisterService

        self.logger.debug("handle_register ", extra={'lvl': 3})

        dependency = self.app.state.services
        p = RegisterService(auth_register_post_request, dependencies=dependency)
        return p.response
    


    

    def handle_get_user_report_linechart(self, user_id, period_type, country  ):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.country = country
        
        from impl.services.admin.get_file_report_total_service import GetFileReportTotalService
    
        dependency = self.app.state.services

        mr = MyRequest()
        p = GetFileReportTotalService(mr, dependencies=dependency)

        return p.response
    

    def handle_get_new_bank_requests(self, user_id, country, start_date, end_date ):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.country = country
                self.start_date = start_date
                self.end_date = end_date
        
        from impl.services.admin.get_new_bank_requests_service import GetNewBankRequestsService
    
        dependency = self.app.state.services

        mr = MyRequest()
        p = GetNewBankRequestsService(mr, dependencies=dependency)

        return p.response


    def handle_get_file_report_total(self, user_id, start_date, end_date,country,bank_id, status):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.start_date = start_date
                self.end_date = end_date
                self.country = country
                self.bank_id = bank_id
                self.status = status
           
        
        from impl.services.admin.get_file_report_total_service import GetFileReportTotalService
    
        dependency = self.app.state.services

        mr = MyRequest()
        p = GetFileReportTotalService(mr, dependencies=dependency)

        return p.response


    def handle_get_file_report_linechart(self, user_id, period_type, start_date,end_date,country,bank_id, status):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.period_type = period_type
                self.start_date = start_date
                self.end_date = end_date
                self.country = country
                self.bank_id = bank_id
                self.status = status
           
        
        from impl.services.admin.get_file_report_linechart_service import GetFileReportLinechartService
    
        dependency = self.app.state.services

        mr = MyRequest()
        p = GetFileReportLinechartService(mr, dependencies=dependency)

        return p.response
        
    

    

    def handle_get_user_profile(self, user_id,):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
            
        from impl.services.user.profile_service import UserProfileService
    
        dependency = self.app.state.services

        mr = MyRequest()
        p = UserProfileService(mr, dependencies=dependency)

        return p.response

    def handle_download_file_by_file_id(self, user_id, file_id, secret_key_for_file_download):
        class MyRequest:
            def __init__(self):
                self.user_id = user_id
                self.file_id = file_id
                self.secret_key_for_file_download = secret_key_for_file_download
        
        from impl.services.admin.download_file_service import DownloadFileService
    
        dependency = self.app.state.services

        mr = MyRequest()
        p = DownloadFileService(mr, dependencies=dependency)

        return p.response

    
    def handle_login_with_refresh(self, email, password, response):
        class MyRequest:
            def __init__(self):
                self.email = email
                self.password = password
        
        from impl.services.auth.login_with_refresh_service import LoginWithRefreshService
        dependency = self.app.state.services


        mr = MyRequest()
        # p = LoginWithRefreshService(mr, dependencies=dependency)
        p = LoginWithRefreshService(mr, dependencies=dependency, response=response)
    
        return p.response

    def handle_login(self, email, password):
        class MyRequest:
            def __init__(self):
                self.email = email
                self.password = password

        from impl.services.auth.login_service import LoginService
        dependency = self.app.state.services

        mr = MyRequest()
        p = LoginService(mr, dependencies=dependency)

        return p.response

    def handle_reset_password(self, auth_reset_password_post_request):
        self.logger.debug("handle_verify_email ", extra={'lvl': 3})


        from impl.services.auth.user_services import ResetPasswordService
        p=ResetPasswordService(auth_reset_password_post_request)
        return p.response


    def handle_verify_email(self, token):


        self.logger.debug("handle_verify_email ", extra={'lvl': 3})
       # self.logger.debug("Total ready records =%s ", self.record_manager.get_number_of_ready_records(), extra={'lvl': 2})

        class MyRequest :
            def __init__(self, logger):
                self.token=token
                self.logger= logger

        mr = MyRequest(self.logger)

        from impl.services.auth.user_services import VerifyService

        p= VerifyService(mr)
        return p.response
    
    def handle_upload_file(self,pdf_file,extension, user_id ,bank_id,  country_code, process_as_test, use_auto_extractor) :

        class MyRequest :
            def __init__(self):
                self.pdf_file=pdf_file
                self.user_id = user_id

                self.bank_id = bank_id
                self.extension = extension
                self.country_code=country_code
                self.process_as_test = process_as_test
                self.use_auto_extractor = use_auto_extractor
        
        from impl.services.file.upload_file_service import UploadFileService

        dependency = self.app.state.services

        mr=MyRequest()
        p =UploadFileService(mr,dependency )

        return p.response
    
    def handle_upload_file_background(self,pdf_file,extension, user_id ,bank_id,  country_code, process_as_test,user_proposed_bank_name, use_auto_extractor, background_tasks) :

        class MyRequest :
            def __init__(self):
                self.pdf_file=pdf_file
                self.user_id = user_id

                self.bank_id = bank_id
                self.extension = extension
                self.country_code=country_code
                self.process_as_test = process_as_test
                self.user_proposed_bank_name = user_proposed_bank_name
                self.use_auto_extractor = use_auto_extractor
                self.background_tasks = background_tasks


        from impl.services.file.upload_file_service_background import UploadFileBackgroundService

        dependency = self.app.state.services

        mr=MyRequest()
        p =UploadFileBackgroundService(mr,dependency )

        return p.response


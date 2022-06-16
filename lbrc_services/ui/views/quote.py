from flask_security import roles_required
from lbrc_flask.forms import ConfirmForm
from flask import redirect, render_template, request, url_for
from flask_login import current_user
from lbrc_services.model.quotes import Quote, QuoteRequirement, QuoteRequirementType, QuoteStatus, QuoteStatusType
from lbrc_flask.database import db
from lbrc_services.model.security import ROLE_QUOTER
from lbrc_services.model.services import Organisation
from lbrc_services.ui.forms import QuoteRequirementForm, QuoteSearchForm, QuoteUpdateForm, QuoteUpdateStatusForm
from lbrc_services.ui.views import _get_quote_query, send_quote_export
from lbrc_flask.json import validate_json
from .. import blueprint


@blueprint.route("/quotes")
@roles_required(ROLE_QUOTER)
def quotes():
    search_form = QuoteSearchForm(formdata=request.args)

    q = _get_quote_query(search_form=search_form)

    quotes = q.paginate(
            page=search_form.page.data,
            per_page=5,
            error_out=False,
        )

    return render_template(
        "ui/quote/index.html",
        quotes=quotes,
        search_form=search_form,
        quote_update_status_form=QuoteUpdateStatusForm(),
    )



@blueprint.route("/quotes/export")
def quotes_export():
    search_form = QuoteSearchForm(formdata=request.args)
    q = _get_quote_query(search_form=search_form, owner_id=current_user.id, sort_asc=True)

    return send_quote_export('My Jobs', q.all())


@blueprint.route("/quotes/update_status", methods=["POST"])
def quote_update_status():
    quote_update_status_form = QuoteUpdateStatusForm()

    print(quote_update_status_form.data)

    if quote_update_status_form.validate_on_submit():
        status_type = QuoteStatusType.query.get_or_404(quote_update_status_form.status_type_id.data)

        update_quote_status(
            quote_update_status_form.quote_id.data,
            status_type,
            quote_update_status_form.notes.data,
        )

    return redirect(request.args.get('prev', ''))


def update_quote_status(quote_id, new_quote_status_type, notes):
        quote = Quote.query.get_or_404(quote_id)

        quote_status = QuoteStatus(
            quote=quote,
            quote_status_type=new_quote_status_type,
            notes=notes,
        )

        db.session.add(quote_status)

        quote.current_status_type = new_quote_status_type

        db.session.add(quote)
        db.session.commit()


@blueprint.route("/quotes/<int:quote_id>/status_history")
def quote_status_history(quote_id):
    quote_statuses = QuoteStatus.query.filter(QuoteStatus.quote_id == quote_id).order_by(QuoteStatus.created_date.desc()).all()

    return render_template("ui/_status_history.html", quote_statuses=quote_statuses)


def save_quote(quote, form, context):

    quote.requestor_id = form.requestor_id.data
    quote.organisation_id = form.organisation_id.data
    quote.organisation_description = form.organisation_description.data
    quote.name = form.name.data

    db.session.add(quote)

    quote_status = QuoteStatus(
        quote=quote,
        quote_status_type=quote.current_status_type,
        notes='Task {} by {}'.format(context, current_user.full_name),
    )

    db.session.add(quote_status)
    db.session.commit()


@blueprint.route("/quotes/create", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def create_quote():
    form = QuoteUpdateForm()

    if form.validate_on_submit():
        quote = Quote(
            current_status_type=QuoteStatusType.get_draft(),
        )

        save_quote(quote, form, 'created')

        return redirect(url_for("ui.quotes"))

    return render_template(
        "ui/quote/create.html",
        form=form,
        other_organisation=Organisation.get_other(),
    )


@blueprint.route("/quotes/<int:quote_id>/edit", methods=["GET", "POST"])
@roles_required(ROLE_QUOTER)
def edit_quote(quote_id):
    quote = Quote.query.get_or_404(quote_id)

    form = QuoteUpdateForm(obj=quote)

    if form.validate_on_submit():

        save_quote(quote, form, 'updated')

        return redirect(request.args.get('prev', ''))

    return render_template(
        "ui/quote/create.html",
        form=form,
        other_organisation=Organisation.get_other(),
    )


@blueprint.route("/quotes/<int:quote_id>/requirements")
@roles_required(ROLE_QUOTER)
def edit_quote_requirements(quote_id):
    return render_template(
        "ui/quote/requirements.html",
        quote=Quote.query.get_or_404(quote_id),
        quote_edit_form=QuoteRequirementForm(),
        delete_form=ConfirmForm(),
    )


@blueprint.route("/quotes/requirements/create", methods=["POST"])
@roles_required(ROLE_QUOTER)
def create_quote_requirement():
    form = QuoteRequirementForm()

    if form.validate_on_submit():
        quote = Quote.query.get_or_404(form.quote_id.data)
        requirement_type = QuoteRequirementType.query.get_or_404(form.quote_requirement_type_id.data)

        requirement = QuoteRequirement.query.filter(QuoteRequirement.id == form.id.data).one_or_none()

        if not requirement:
            print('Ole beyonmd his years')
            requirement = QuoteRequirement(
                quote=quote,
            )

        requirement.quote_requirement_type = requirement_type
        requirement.notes = form.notes.data

        db.session.add(requirement)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))


@blueprint.route("/quotes/requirements/delete", methods=['POST'])
def delete_quote_requirement():
    form = ConfirmForm()

    if form.validate_on_submit():
        r = QuoteRequirement.query.get_or_404(form.id.data)
        db.session.delete(r)
        db.session.commit()

    return redirect(request.args.get('prev', url_for('ui.quotes')))

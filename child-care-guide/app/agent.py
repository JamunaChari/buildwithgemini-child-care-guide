# ruff: noqa
# Copyright 2026 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import datetime
import json
import os
import uuid
from zoneinfo import ZoneInfo

from a2ui.basic_catalog.provider import BasicCatalog
from a2ui.schema.manager import A2uiSchemaManager
from google import genai
from google.adk.agents import Agent
from google.adk.apps import App
from google.adk.models import Gemini
from google.adk.tools import ToolContext
from google.cloud import storage
from google.genai import types

from .a2ui_utils import a2ui_callback


MODEL = "gemini-3.6-flash"


def get_milestones_and_care_steps(age_months: int) -> str:
    """Retrieves developmental milestones and essential care steps for a given age in months.

    Args:
        age_months: Age of the child in months (e.g., 2, 4, 6, 9, 12, 18, 24).

    Returns:
        A detailed summary of physical, cognitive, social, and language milestones, plus recommended care steps.
    """
    if age_months <= 2:
        return (
            "**2 Months Milestones & Care Steps:**\n"
            "- **Social/Emotional:** Smiles at people, tries to look at parents.\n"
            "- **Language/Communication:** Coos, makes gurgling sounds, turns head toward sounds.\n"
            "- **Cognitive:** Pays attention to faces, begins to follow things with eyes.\n"
            "- **Movement/Physical:** Can hold head up and begins to push up when lying on tummy.\n"
            "- **Care Steps:** Practice daily tummy time (3-5 mins), talk and sing regularly, ensure safe sleep on back in crib."
        )
    elif age_months <= 5:
        return (
            "**4-5 Months Milestones & Care Steps:**\n"
            "- **Social/Emotional:** Smiles spontaneously, likes to play with people, copies some movements/facial expressions.\n"
            "- **Language/Communication:** Begins to babble, cries in different ways to show hunger, pain, or tiredness.\n"
            "- **Cognitive:** Responds to affection, reaches for toy with one hand, uses hands and eyes together.\n"
            "- **Movement/Physical:** Holds head steady unsupported, pushes down on legs when feet are on a hard surface, rolls from tummy to back.\n"
            "- **Care Steps:** Provide colorful toys to reach for, maintain consistent feeding/nap routine, continue supervised tummy time."
        )
    elif age_months <= 8:
        return (
            "**6-8 Months Milestones & Care Steps:**\n"
            "- **Social/Emotional:** Knows familiar faces, likes to look at self in a mirror.\n"
            "- **Language/Communication:** Responds to own name, makes vowel sounds together ('ah', 'eh', 'oh'), takes turns making sounds.\n"
            "- **Cognitive:** Brings things to mouth, shows curiosity about things and tries to get things out of reach.\n"
            "- **Movement/Physical:** Rolls over in both directions, begins to sit without support, supports weight on legs when standing.\n"
            "- **Care Steps:** Introduce single-ingredient solid foods (iron-fortified cereals, purees), baby-proof low cabinets and outlets, play peek-a-boo."
        )
    elif age_months <= 11:
        return (
            "**9-11 Months Milestones & Care Steps:**\n"
            "- **Social/Emotional:** May be afraid of strangers, has favorite toys.\n"
            "- **Language/Communication:** Understands 'no', makes lots of different sounds ('mamama', 'bababa'), uses fingers to point.\n"
            "- **Cognitive:** Watches the path of something as it falls, plays peek-a-boo, moves items smoothly from one hand to another.\n"
            "- **Movement/Physical:** Stands holding on, pulls up to stand, crawls.\n"
            "- **Care Steps:** Encourage finger foods (soft fruits, cooked veggies), read simple picture books, practice pincer grasp with safe foods."
        )
    elif age_months <= 17:
        return (
            "**12-17 Months Milestones & Care Steps:**\n"
            "- **Social/Emotional:** Hands a book to an adult when wants to hear a story, repeats sounds or actions to get attention.\n"
            "- **Language/Communication:** Says 'mama' and 'dada' and 1-2 other words, uses simple gestures like shaking head 'no' or waving 'bye-bye'.\n"
            "- **Cognitive:** Explores things in different ways (shaking, banging, throwing), finds hidden objects easily.\n"
            "- **Movement/Physical:** Walks holding onto furniture ('cruising'), may take a few steps without support, drinks from a cup.\n"
            "- **Care Steps:** Transition to whole cow's milk or fortified milk substitute (consult pediatrician), encourage independent walking, establish bedtime reading routine."
        )
    else:
        return (
            f"**{age_months} Months (Toddler) Milestones & Care Steps:**\n"
            "- **Social/Emotional:** Copies others, shows more independence, displays excitement around other children.\n"
            "- **Language/Communication:** Points to things when named, knows names of familiar people/body parts, says short phrases (2-4 words).\n"
            "- **Cognitive:** Sorts shapes and colors, completes sentences and rhymes in familiar books, builds towers of 4+ blocks.\n"
            "- **Movement/Physical:** Kicks a ball, runs, walks up and down stairs holding on.\n"
            "- **Care Steps:** Offer balanced family meals, set gentle boundaries, encourage pretend play, limit screen time according to pediatric guidelines."
        )


def get_age_appropriate_activities(age_months: int, category: str = "all") -> str:
    """Provides recommended play, sensory, and bonding activities for a child based on age in months.

    Args:
        age_months: Age of the child in months.
        category: Activity category, e.g., 'sensory', 'motor', 'bonding', or 'all'.

    Returns:
        Recommended fun and educational activities tailored to the child's developmental stage.
    """
    if age_months < 4:
        return (
            "**Activities for 0-3 Months:**\n"
            "1. **Tummy Time Mirror Play:** Place a unbreakable baby mirror in front during tummy time to encourage head lifting.\n"
            "2. **High-Contrast Tracking:** Slow-move black-and-white cards or high-contrast toys across their field of vision.\n"
            "3. **Sing & Soft Touch:** Sing gentle nursery rhymes while gently massaging fingers and toes."
        )
    elif age_months < 9:
        return (
            "**Activities for 4-8 Months:**\n"
            "1. **Peek-a-Boo:** Use a soft cloth to play peek-a-boo, developing object permanence.\n"
            "2. **Textured Touch Bags:** Fill sealable bags with water, gel, or soft pom-poms for sensory exploration on a tray.\n"
            "3. **Sit & Reach:** Place colorful toys just out of reach while baby is sitting supported to practice balance."
        )
    elif age_months < 15:
        return (
            "**Activities for 9-14 Months:**\n"
            "1. **Container Drop:** Practice dropping large wooden blocks or soft balls into an open tub and taking them out.\n"
            "2. **Obstacle Course Crawl:** Arrange pillows and cushions on a soft rug for baby to climb over.\n"
            "3. **Interactive Reading:** Read lift-the-flap or touch-and-feel books, naming animals and objects."
        )
    else:
        return (
            f"**Activities for {age_months} Months:**\n"
            "1. **Color Sorting Game:** Group soft balls or big plastic cups by basic colors.\n"
            "2. **Pretend Kitchen/Tea Party:** Encourage pretend play with play dishes and stuffed animals.\n"
            "3. **Outdoor Nature Walk:** Point out birds, leaves, and flowers, encouraging naming and vocabulary."
        )


def calculate_child_age(birth_date: str) -> str:
    """Calculates exact age in months and days from a birthdate string (YYYY-MM-DD).

    Args:
        birth_date: Birthdate in YYYY-MM-DD format (e.g. '2025-08-15').

    Returns:
        Calculated age formatted in months, weeks, and days.
    """
    try:
        bdate = datetime.datetime.strptime(birth_date, "%Y-%m-%d").date()
        today = datetime.date.today()
        if bdate > today:
            return "Birthdate cannot be in the future."
        
        days_diff = (today - bdate).days
        months = days_diff // 30
        weeks = (days_diff % 30) // 7
        remaining_days = (days_diff % 30) % 7
        
        return f"The child is approximately {months} month(s), {weeks} week(s), and {remaining_days} day(s) old ({days_diff} days total)."
    except Exception as e:
        return f"Error parsing birthdate '{birth_date}'. Please format as YYYY-MM-DD."


def get_south_indian_veg_diet_guide() -> str:
    """Provides South Indian vegetarian nutrition and meal ideas rich in protein, iron, calcium, and healthy fats.

    Returns:
        Recommended toddler-friendly South Indian vegetarian meal and snack ideas.
    """
    return (
        "**South Indian Vegetarian Nutrition Guide for Toddlers:**\n"
        "- **Breakfast Ideas:** Soft mini Idlis with ghee and mild tomato/lentil chutney, Ragi (finger millet) porridge made with milk/jaggery, or soft Rava/Oats Dosa.\n"
        "- **Lunch Ideas:** Soft Curd Rice topped with grated carrots/beetroot and a drop of ghee, Moong Dal Khichdi with mashed spinach/carrots, or Sambar Rice made with mild veggies and ghee.\n"
        "- **Snacks & Finger Foods:** Steamed Steamed Kozhukattai/Modak, Paneer/Tofu cubes, roasted Makhana (fox nuts), mashed avocado/banana, or boiled sweet potato slices.\n"
        "- **Dinner Ideas:** Soft Uttapam with grated vegetables, Dhal/Rasam rice with mashed potatoes or beans, or Dosa with mild dhal.\n"
        "- **Nutritional Focus:** Ensure good sources of protein (lentils/dhal, paneer, curd, chickpeas) and iron (spinach, ragi, jaggery, amaranth) paired with Vitamin C (lemon, tomatoes) for optimal absorption."
    )


def get_high_energy_toddler_activities() -> str:
    """Provides active indoor and outdoor physical activities tailored for super energetic toddlers.

    Returns:
        High-energy physical games, music/dance activities, and sensory play ideas.
    """
    return (
        "**High-Energy Play Activities for Active Toddlers:**\n"
        "1. **Pillow & Cushion Obstacle Course:** Set up soft pillows and couch cushions on a rug for crawling, climbing, and jumping over safely.\n"
        "2. **Freeze Dance & Rhythm Party:** Play energetic South Indian nursery rhymes or songs; practice freeze dance when the music stops.\n"
        "3. **Animal Hops & Walks:** Practice pretending to be different animals—frog hops, duck waddles, and kangaroo jumps across the room.\n"
        "4. **Soft Ball Chase & Kick:** Roll or kick a light beach ball or soft foam ball across a hallway or garden.\n"
        "5. **Outdoor Nature Dash:** Go to a safe park or grassy lawn for running, leaf collecting, and chasing bubbles."
    )


def get_book_recommendations_for_toddlers() -> str:
    """Provides curated picture book recommendations for toddlers aged 2 to 3 years old.

    Returns:
        A list of top interactive, rhythmic, sensory, and culturally rich toddler books.
    """
    return (
        "**Curated Book Recommendations for 2-3 Year Old Toddlers:**\n\n"
        "📚 **Interactive & Lift-the-Flap Books:**\n"
        "- *Where Is Baby's Belly Button?* by Karen Katz (Fun interactive lift-the-flap)\n"
        "- *Dear Zoo* by Rod Campbell (Classic flap book featuring different animals)\n"
        "- *Press Here* by Hervé Tullet (Interactive, encouraging finger pressing and shaking)\n\n"
        "🎵 **Rhyming & Repetitive Favorites:**\n"
        "- *Brown Bear, Brown Bear, What Do You See?* by Bill Martin Jr. & Eric Carle\n"
        "- *The Very Hungry Caterpillar* by Eric Carle (Colors, counting, and days of the week)\n"
        "- *Chicka Chicka Boom Boom* by Bill Martin Jr. & John Archambault (Rhythmic alphabet rhyme)\n"
        "- *Barnyard Dance!* by Sandra Boynton (Energetic dancing animals rhyme)\n\n"
        "🌟 **Indian & Culturally Inclusive Toddler Books:**\n"
        "- *Gajapati Kulapati* by Ashok Rajagopalan (Hilarious, rhythmic story of a friendly elephant that toddlers love!)\n"
        "- *Amma, Tell Me About Ganesha!* by Bhakti Mathur (Colorful introduction to Indian heritage)\n"
        "- *Farmer Falgu Goes to the Market* by Chitra Soundar (Charming South Asian storytelling with sound effects)\n"
        "- *What Shall I Wear Today?* by Tulika Books (Simple daily routine book for toddlers)\n\n"
        "💛 **Emotional & Daily Routine Books:**\n"
        "- *The Going to Bed Book* by Sandra Boynton (Soothing bedtime routine story)\n"
        "- *Llama Llama Red Pajama* by Anna Dewdney (Comforting story about nighttime independence)\n"
        "- *Potty* by Leslie Patricelli (Fun and encouraging book about potty readiness)"
    )


def get_karnataka_veg_weekly_plan() -> str:
    """Provides a complete weekly plan tailored for a toddler, including a Karnataka vegetarian meal plan, sleep routine, and developmental play activities.

    Returns:
        A comprehensive 7-day plan with Karnataka vegetarian meals, consistent sleep schedules, and high-energy developmental activities.
    """
    return (
        "**Comprehensive Weekly Plan for Toddlers (Karnataka Vegetarian Diet, Sleep & Activities):**\n\n"
        "⏰ **Consistent Daily Sleep Routine:**\n"
        "- **7:00 AM - 7:30 AM:** Morning Wake Up\n"
        "- **1:00 PM - 3:00 PM:** Afternoon Nap (2 hours of restful sleep)\n"
        "- **7:30 PM - 8:30 PM:** Bedtime Wind-Down (Warm bath, book reading, dim lights, asleep by 8:30 PM)\n"
        "- *Total Recommended Sleep:* 12–13 hours per 24-hour period.\n\n"
        "🍽️ **7-Day Karnataka Vegetarian Meal Plan:**\n"
        "- **Monday:**\n"
        "  • Breakfast: Warm Ragi Porridge with milk, jaggery, cardamom, and ghee.\n"
        "  • Lunch: Soft Bisi Bele Bath (mild rice, lentils, carrots, pumpkin) with ghee.\n"
        "  • Snack: Steamed Rice Kadubu / Kozhukattai with soft banana.\n"
        "  • Dinner: Soft Akki Rotti / Rava Dosa with mild Toor Dhal.\n\n"
        "- **Tuesday:**\n"
        "  • Breakfast: Soft Mini Idlis with ghee and mild Tomato/Moong Dhal Chutney.\n"
        "  • Lunch: Curd Rice topped with grated beetroot/carrot and mild cumin seasoning.\n"
        "  • Snack: Roasted Makhana (Fox nuts) in ghee & Paneer cubes.\n"
        "  • Dinner: Vegetable Set Dosa with mild Sambar.\n\n"
        "- **Wednesday:**\n"
        "  • Breakfast: Wheat Rava / Oats Upma with finely chopped veggies.\n"
        "  • Lunch: Moong Dal & Palak (Spinach) Khichdi with a generous dollop of ghee.\n"
        "  • Snack: Steamed Sweet Potato slices & fruit mash.\n"
        "  • Dinner: Soft Phulka / Chapati mashed in Hesaru Bele (Moong Dal) Kootu.\n\n"
        "- **Thursday:**\n"
        "  • Breakfast: Ragi Dosa / Ragi Rotti made with mild grated carrots.\n"
        "  • Lunch: Soft Sambar Rice with ghee & boiled Chow-Chow (Chayote squash).\n"
        "  • Snack: Mashed Avocado & Banana with soaked/blended nuts.\n"
        "  • Dinner: Soft Uttapam served with mild Dhal.\n\n"
        "- **Friday:**\n"
        "  • Breakfast: Soft Avalakki (Poha Upma) with mild turmeric and green peas.\n"
        "  • Lunch: Soft Rice with Majjige Huli (curd/buttermilk vegetable stew) & ghee.\n"
        "  • Snack: Boiled Hesaru Kalu (Green Gram) / Chana Sundal.\n"
        "  • Dinner: Wheat Dosa with mild tomato dhal.\n\n"
        "- **Saturday:**\n"
        "  • Breakfast: Vegetable Uttapam / Paddu (Appe) with mild chutney.\n"
        "  • Lunch: Chitranna (Mild Lemon Rice) mashed soft, served with fresh curd.\n"
        "  • Snack: Steamed Sweet Corn & Paneer bites.\n"
        "  • Dinner: Soft Idlis with Rasam Rice / mild Dhal.\n\n"
        "- **Sunday:**\n"
        "  • Breakfast: Soft Puri with mild Potato/Sweet Potato Masala.\n"
        "  • Lunch: Soft Moong Dal Khichdi served with Kosambari (soaked soft moong dal with cucumber).\n"
        "  • Snack: Steamed Modak / Rice dumplings with fruit slice.\n"
        "  • Dinner: Soft Dosa with mild Sambar and ghee.\n\n"
        "🏃‍♀️ **Weekly Developmental & High-Energy Activities:**\n"
        "- **Mon & Thu (Motor & Coordination):** Pillow & Cushion Obstacle Course indoors; ball kicking & chasing in the hallway.\n"
        "- **Tue & Fri (Music & Rhythm):** Freeze Dance to energetic South Indian rhymes; animal hops & walks (frog, kangaroo, elephant).\n"
        "- **Wed & Sat (Sensory & Cognitive):** Color sorting game with soft balls; water/gel sensory bag play on tray.\n"
        "- **Sun (Outdoor & Language):** Park Nature Dash, chasing soap bubbles, pointing and naming birds and trees during stroller walks."
    )


MILESTONES_FILE = os.path.join(os.path.dirname(__file__), "..", "milestones_log.json")


def save_child_milestone_log(milestone_name: str, date_achieved: str = "", notes: str = "") -> str:
    """Saves a newly achieved developmental milestone for the child to persistent local storage.

    Args:
        milestone_name: Description of the achieved milestone (e.g. 'Jumped with both feet off the floor', 'Said first 3-word phrase').
        date_achieved: Date achieved in YYYY-MM-DD format (defaults to today's date if omitted).
        notes: Optional extra observations or context (e.g. 'Did it while playing in the living room').

    Returns:
        Confirmation message that the milestone was successfully saved.
    """
    if not date_achieved:
        date_achieved = datetime.date.today().isoformat()

    entry = {
        "milestone_name": milestone_name,
        "date_achieved": date_achieved,
        "notes": notes,
        "logged_at": datetime.datetime.now().isoformat(),
    }

    logs = []
    if os.path.exists(MILESTONES_FILE):
        try:
            with open(MILESTONES_FILE, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    logs.append(entry)

    os.makedirs(os.path.dirname(MILESTONES_FILE), exist_ok=True)
    with open(MILESTONES_FILE, "w") as f:
        json.dump(logs, f, indent=2)

    return f"✅ Successfully logged milestone: '{milestone_name}' (Date: {date_achieved})."


def get_logged_child_milestones() -> str:
    """Retrieves all previously logged developmental milestones for the child from persistent storage.

    Returns:
        A list of all logged milestones with dates and notes, or a message if none are logged yet.
    """
    if not os.path.exists(MILESTONES_FILE):
        return "No milestones have been logged yet."

    try:
        with open(MILESTONES_FILE, "r") as f:
            logs = json.load(f)
        if not logs:
            return "No milestones have been logged yet."

        summary = "**Logged Milestones History:**\n"
        for idx, item in enumerate(logs, 1):
            summary += f"{idx}. **{item['milestone_name']}** (Achieved: {item['date_achieved']})"
            if item.get("notes"):
                summary += f" - *Notes:* {item['notes']}"
            summary += "\n"
        return summary
    except Exception as e:
        return f"Error reading logged milestones: {e}"


STATIC_ASSETS_BUCKET = "qwiklabs-gcp-03-17692a0e1a33-static-assets-bucket"


async def generate_activity_visual_guide(prompt: str, tool_context: ToolContext) -> str:
    """Generates an illustrative visual play and activity guide card for toddlers.

    Args:
        prompt: Description of the activity or visual play guide to generate (e.g. 'Obstacle course with soft cushions', 'Color sorting game with soft balls').

    Returns:
        The public HTTPS Cloud Storage URL of the generated visual activity image.
    """
    client = genai.Client(vertexai=True, location="global")
    response = client.models.generate_content(
        model="gemini-3.1-flash-lite-image",
        contents=f"A vibrant, child-friendly, illustrative toddler activity guide card: {prompt}",
        config=types.GenerateContentConfig(response_modalities=["IMAGE"]),
    )

    image_bytes = None
    if response.candidates:
        for candidate in response.candidates:
            if candidate.content and candidate.content.parts:
                for part in candidate.content.parts:
                    if part.inline_data and part.inline_data.data:
                        image_bytes = part.inline_data.data
                        break

    if not image_bytes:
        return "Failed to generate activity visual guide image."

    filename = f"activity_{uuid.uuid4().hex[:8]}.jpg"

    # (1) Save artifact so it appears in Playground's Artifacts panel
    artifact_part = types.Part(inline_data=types.Blob(mime_type="image/jpeg", data=image_bytes))
    await tool_context.save_artifact(filename, artifact_part)

    # (2) Upload same image bytes to public Cloud Storage bucket and return public HTTPS URL
    storage_client = storage.Client()
    bucket = storage_client.bucket(STATIC_ASSETS_BUCKET)
    blob = bucket.blob(f"activities/{filename}")
    blob.upload_from_string(image_bytes, content_type="image/jpeg")

    public_url = f"https://storage.googleapis.com/{STATIC_ASSETS_BUCKET}/activities/{filename}"
    return public_url


schema_manager = A2uiSchemaManager(
    version="0.8",
    catalogs=[BasicCatalog.get_config("0.8")],
)

instruction = schema_manager.generate_system_prompt(
    role_description=(
        "You are LittleSteps, a personalized Child Care & Developmental Milestone Assistant. "
        "You are helping a loving parent of a super energetic toddler girl born on May 8, 2024 "
        "(Height: 3 ft 3 in / ~99 cm, Weight: 33.2 lbs / ~15 kg). "
        "The family follows a Karnataka Vegetarian diet, and the daughter loves book reading."
    ),
    workflow_description=(
        "Provide warm, encouraging, and actionable weekly guidance incorporating authentic Karnataka vegetarian nutrition, "
        "sleep routines, high-energy play activities, book recommendations, and milestone advice. "
        "Use your available tools to generate activity visual guides, log new milestones, review logged milestone history, "
        "look up weekly plans, dietary guidelines, high-energy activities, book lists, or calculate age when dates are provided."
    ),
    ui_description=(
        "Keep every surface tiny and flat: ONE Card > ONE Column > a few Text rows. "
        "Never nest a Card inside a Card. "
        "Use ONLY these components: Card, Column, Row, Text, and Image. Do not use "
        "Table or Heading (unsupported), or Buttons, actions, or forms (they do "
        "nothing in adk web). "
        "You may include one Image component, but only when you have a public https "
        "URL for the image (for example the URL an image tool returns after uploading "
        "to a public bucket). Set the Image url to that exact https link, for example "
        "{\"Image\": {\"url\": {\"literalString\": \"https://...\"}}}. Never point an "
        "Image at a bare filename, an artifact name, or a non-http(s) path. If you do "
        "not have a public URL, add a short Text line noting the image instead. "
        "No markdown in text; use the usageHint property ('h1', 'h2', 'body') for "
        "headings and emphasis. "
        "Output ONLY the raw A2UI JSON array — no prose, and never wrap it in "
        "<a2a_datapart_json> tags or 'kind'/'data'/'metadata' objects."
    ),
    include_schema=True,
    include_examples=True,
)


root_agent = Agent(
    name="root_agent",
    model=Gemini(
        model=MODEL,
        retry_options=types.HttpRetryOptions(attempts=3),
    ),
    instruction=instruction,
    tools=[
        get_milestones_and_care_steps,
        get_age_appropriate_activities,
        calculate_child_age,
        get_south_indian_veg_diet_guide,
        get_high_energy_toddler_activities,
        get_book_recommendations_for_toddlers,
        get_karnataka_veg_weekly_plan,
        save_child_milestone_log,
        get_logged_child_milestones,
        generate_activity_visual_guide,
    ],
    after_model_callback=a2ui_callback,
)

app = App(
    root_agent=root_agent,
    name="app",
)
